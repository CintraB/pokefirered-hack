/*
 * mgba_runner: roda uma ROM de GBA sem janela (libmgba) e obedece comandos
 * JSON lidos do stdin, uma linha por comando, respondendo uma linha JSON no
 * stdout: {"ok":true,...} ou {"ok":false,"error":"..."}.
 *
 * Uso: mgba_runner <rom.gba> --save <arquivo.sav>
 *
 * Comandos:
 *   {"cmd":"frames","n":N}              -> {"ok":true,"frame":F}
 *   {"cmd":"keys","mask":M}             (mantido até o próximo "keys")
 *   {"cmd":"read","addr":A,"len":L}     -> {"ok":true,"hex":"..."}
 *   {"cmd":"write","addr":A,"hex":"..."}
 *   {"cmd":"screenshot","path":"x.png"} (PNG 240x160)
 *   {"cmd":"state_save","path":"x.ss"}
 *   {"cmd":"state_load","path":"x.ss"}
 *   {"cmd":"reset"}
 *   {"cmd":"flush_save"}                (grava agora no .sav o save do jogo que está na memória)
 *   {"cmd":"quit"}                      (grava o .sav e sai)
 */
#include <mgba/flags.h> /* define USE_PNG antes de png-io.h */
#include <mgba/core/core.h>
#include <mgba/core/log.h>
#include <mgba/core/serialize.h>
#include <mgba-util/png-io.h>
#include <mgba-util/vfs.h>

#include <ctype.h>
#include <errno.h>
#include <fcntl.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#define SCREEN_W 240
#define SCREEN_H 160
#define MAX_READ_LEN (16 * 1024 * 1024)
#define STATE_FLAGS (SAVESTATE_SAVEDATA | SAVESTATE_RTC)

static color_t sVideoBuffer[SCREEN_W * SCREEN_H];

/* ---------- log: nunca no stdout (o stdout é o canal do protocolo) ---------- */

static void QuietLog(struct mLogger *logger, int category, enum mLogLevel level, const char *format, va_list args)
{
    (void)logger;
    if (!(level & (mLOG_FATAL | mLOG_ERROR)))
        return;
    fprintf(stderr, "[mgba %s] ", mLogCategoryName(category));
    vfprintf(stderr, format, args);
    fputc('\n', stderr);
}

static struct mLogger sLogger = { .log = QuietLog, .filter = NULL };

/* ---------- JSON mínimo: objeto plano com valores string ou inteiro ---------- */

#define MAX_FIELDS 8

struct Field {
    char key[32];
    int isString;
    long long num;
    char *str; /* alocado; NULL se não for string */
};

struct Command {
    int count;
    struct Field fields[MAX_FIELDS];
};

static void FreeCommand(struct Command *cmd)
{
    for (int i = 0; i < cmd->count; i++)
        free(cmd->fields[i].str);
    cmd->count = 0;
}

static const char *SkipWs(const char *p)
{
    while (*p && isspace((unsigned char)*p))
        p++;
    return p;
}

static void AppendUtf8(char **out, unsigned cp)
{
    char *o = *out;
    if (cp < 0x80) {
        *o++ = (char)cp;
    } else if (cp < 0x800) {
        *o++ = (char)(0xC0 | (cp >> 6));
        *o++ = (char)(0x80 | (cp & 0x3F));
    } else {
        *o++ = (char)(0xE0 | (cp >> 12));
        *o++ = (char)(0x80 | ((cp >> 6) & 0x3F));
        *o++ = (char)(0x80 | (cp & 0x3F));
    }
    *out = o;
}

/* Lê uma string JSON a partir de p (que aponta para a aspa). Retorna o ponteiro
 * após a aspa final, ou NULL em erro. O resultado (alocado) vai em *out. */
static const char *ParseString(const char *p, char **out)
{
    if (*p != '"')
        return NULL;
    p++;
    /* UTF-8 de \uXXXX ocupa no máximo 3 bytes para 6 de entrada: cabe em strlen(p)+1. */
    char *buf = malloc(strlen(p) + 1);
    if (!buf)
        return NULL;
    char *o = buf;
    while (*p && *p != '"') {
        if (*p != '\\') {
            *o++ = *p++;
            continue;
        }
        p++;
        switch (*p) {
        case '"': *o++ = '"'; break;
        case '\\': *o++ = '\\'; break;
        case '/': *o++ = '/'; break;
        case 'b': *o++ = '\b'; break;
        case 'f': *o++ = '\f'; break;
        case 'n': *o++ = '\n'; break;
        case 'r': *o++ = '\r'; break;
        case 't': *o++ = '\t'; break;
        case 'u': {
            unsigned cp = 0;
            for (int i = 1; i <= 4; i++) {
                if (!isxdigit((unsigned char)p[i])) {
                    free(buf);
                    return NULL;
                }
                char c = (char)tolower((unsigned char)p[i]);
                cp = cp * 16 + (unsigned)(isdigit((unsigned char)c) ? c - '0' : c - 'a' + 10);
            }
            AppendUtf8(&o, cp);
            p += 4;
            break;
        }
        default:
            free(buf);
            return NULL;
        }
        p++;
    }
    if (*p != '"') {
        free(buf);
        return NULL;
    }
    *o = '\0';
    *out = buf;
    return p + 1;
}

static int ParseCommand(const char *line, struct Command *cmd)
{
    cmd->count = 0;
    const char *p = SkipWs(line);
    if (*p++ != '{')
        return 0;
    p = SkipWs(p);
    if (*p == '}')
        return 1;
    for (;;) {
        if (cmd->count >= MAX_FIELDS)
            return 0;
        struct Field *f = &cmd->fields[cmd->count];
        memset(f, 0, sizeof(*f));
        char *key = NULL;
        p = ParseString(SkipWs(p), &key);
        if (!p)
            return 0;
        snprintf(f->key, sizeof(f->key), "%s", key);
        free(key);
        p = SkipWs(p);
        if (*p++ != ':')
            return 0;
        p = SkipWs(p);
        if (*p == '"') {
            p = ParseString(p, &f->str);
            if (!p)
                return 0;
            f->isString = 1;
        } else {
            char *end;
            errno = 0;
            f->num = strtoll(p, &end, 10);
            if (end == p || errno)
                return 0;
            p = end;
        }
        cmd->count++;
        p = SkipWs(p);
        if (*p == ',') {
            p++;
            continue;
        }
        if (*p == '}')
            return 1;
        return 0;
    }
}

static const struct Field *GetField(const struct Command *cmd, const char *key)
{
    for (int i = 0; i < cmd->count; i++)
        if (strcmp(cmd->fields[i].key, key) == 0)
            return &cmd->fields[i];
    return NULL;
}

static int GetInt(const struct Command *cmd, const char *key, long long *out)
{
    const struct Field *f = GetField(cmd, key);
    if (!f || f->isString)
        return 0;
    *out = f->num;
    return 1;
}

static const char *GetStr(const struct Command *cmd, const char *key)
{
    const struct Field *f = GetField(cmd, key);
    return (f && f->isString) ? f->str : NULL;
}

/* ---------- respostas ---------- */

static void ReplyOk(void)
{
    fputs("{\"ok\":true}\n", stdout);
    fflush(stdout);
}

static void ReplyError(const char *fmt, ...)
{
    char msg[512];
    va_list args;
    va_start(args, fmt);
    vsnprintf(msg, sizeof(msg), fmt, args);
    va_end(args);

    fputs("{\"ok\":false,\"error\":\"", stdout);
    for (const char *c = msg; *c; c++) {
        if (*c == '"' || *c == '\\')
            fputc('\\', stdout);
        if ((unsigned char)*c < 0x20)
            fputc(' ', stdout);
        else
            fputc(*c, stdout);
    }
    fputs("\"}\n", stdout);
    fflush(stdout);
}

/* ---------- comandos ---------- */

static void CmdFrames(struct mCore *core, const struct Command *cmd)
{
    long long n;
    if (!GetInt(cmd, "n", &n) || n < 0) {
        ReplyError("frames: campo \"n\" inteiro >= 0 obrigatório");
        return;
    }
    for (long long i = 0; i < n; i++)
        core->runFrame(core);
    printf("{\"ok\":true,\"frame\":%u}\n", core->frameCounter(core));
    fflush(stdout);
}

static void CmdKeys(struct mCore *core, const struct Command *cmd)
{
    long long mask;
    if (!GetInt(cmd, "mask", &mask) || mask < 0 || mask > 0x3FF) {
        ReplyError("keys: campo \"mask\" entre 0 e 0x3FF obrigatório");
        return;
    }
    core->setKeys(core, (uint32_t)mask);
    ReplyOk();
}

static void CmdRead(struct mCore *core, const struct Command *cmd)
{
    long long addr, len;
    if (!GetInt(cmd, "addr", &addr) || !GetInt(cmd, "len", &len) || addr < 0 || addr > 0xFFFFFFFFLL
        || len < 0 || len > MAX_READ_LEN) {
        ReplyError("read: campos \"addr\" e \"len\" (0..%d) obrigatórios", MAX_READ_LEN);
        return;
    }
    static const char digits[] = "0123456789abcdef";
    char *hex = malloc((size_t)len * 2 + 1);
    if (!hex) {
        ReplyError("read: sem memória");
        return;
    }
    for (long long i = 0; i < len; i++) {
        uint8_t b = (uint8_t)core->busRead8(core, (uint32_t)(addr + i));
        hex[i * 2] = digits[b >> 4];
        hex[i * 2 + 1] = digits[b & 0xF];
    }
    hex[len * 2] = '\0';
    printf("{\"ok\":true,\"hex\":\"%s\"}\n", hex);
    fflush(stdout);
    free(hex);
}

static int HexNibble(char c)
{
    if (c >= '0' && c <= '9')
        return c - '0';
    c = (char)tolower((unsigned char)c);
    if (c >= 'a' && c <= 'f')
        return c - 'a' + 10;
    return -1;
}

static void CmdWrite(struct mCore *core, const struct Command *cmd)
{
    long long addr;
    const char *hex = GetStr(cmd, "hex");
    if (!GetInt(cmd, "addr", &addr) || !hex || addr < 0 || addr > 0xFFFFFFFFLL) {
        ReplyError("write: campos \"addr\" e \"hex\" obrigatórios");
        return;
    }
    size_t len = strlen(hex);
    if (len % 2) {
        ReplyError("write: \"hex\" com número ímpar de dígitos");
        return;
    }
    for (size_t i = 0; i < len; i++) {
        if (HexNibble(hex[i]) < 0) {
            ReplyError("write: \"hex\" contém caractere inválido");
            return;
        }
    }
    for (size_t i = 0; i < len / 2; i++) {
        uint8_t b = (uint8_t)(HexNibble(hex[i * 2]) << 4 | HexNibble(hex[i * 2 + 1]));
        core->busWrite8(core, (uint32_t)(addr + (long long)i), b);
    }
    ReplyOk();
}

static void CmdScreenshot(const struct Command *cmd)
{
    const char *path = GetStr(cmd, "path");
    if (!path) {
        ReplyError("screenshot: campo \"path\" obrigatório");
        return;
    }
    struct VFile *vf = VFileOpen(path, O_CREAT | O_TRUNC | O_WRONLY);
    if (!vf) {
        ReplyError("screenshot: não abriu %s", path);
        return;
    }
    png_structp png = PNGWriteOpen(vf);
    png_infop info = png ? PNGWriteHeader(png, SCREEN_W, SCREEN_H) : NULL;
    bool ok = info && PNGWritePixels(png, SCREEN_W, SCREEN_H, SCREEN_W, sVideoBuffer);
    if (png)
        PNGWriteClose(png, info);
    vf->close(vf);
    if (!ok) {
        ReplyError("screenshot: falha ao gravar PNG em %s", path);
        return;
    }
    ReplyOk();
}

static void CmdStateSave(struct mCore *core, const struct Command *cmd)
{
    const char *path = GetStr(cmd, "path");
    if (!path) {
        ReplyError("state_save: campo \"path\" obrigatório");
        return;
    }
    struct VFile *vf = VFileOpen(path, O_CREAT | O_TRUNC | O_RDWR);
    if (!vf) {
        ReplyError("state_save: não abriu %s", path);
        return;
    }
    bool ok = mCoreSaveStateNamed(core, vf, STATE_FLAGS);
    vf->close(vf);
    if (!ok) {
        ReplyError("state_save: falha ao gravar %s", path);
        return;
    }
    ReplyOk();
}

static void CmdStateLoad(struct mCore *core, const struct Command *cmd)
{
    const char *path = GetStr(cmd, "path");
    if (!path) {
        ReplyError("state_load: campo \"path\" obrigatório");
        return;
    }
    struct VFile *vf = VFileOpen(path, O_RDONLY);
    if (!vf) {
        ReplyError("state_load: não abriu %s", path);
        return;
    }
    bool ok = mCoreLoadStateNamed(core, vf, STATE_FLAGS);
    vf->close(vf);
    if (!ok) {
        ReplyError("state_load: estado inválido em %s", path);
        return;
    }
    ReplyOk();
}

/* O mGBA só garante o .sav em disco ao fechar (deinit). Aqui a cópia do save do jogo que está
 * na memória (savedataClone) é escrita por cima do .sav da sessão, sem truncar nem trocar o
 * arquivo (o mGBA o mantém mapeado), com fsync antes de responder. */
static void CmdFlushSave(struct mCore *core, const char *savePath)
{
    void *sram = NULL;
    size_t size = core->savedataClone(core, &sram);
    if (!size || !sram) {
        free(sram);
        ReplyError("flush_save: o jogo ainda não tem save na memória");
        return;
    }
    int fd = open(savePath, O_WRONLY | O_CREAT, 0644);
    if (fd < 0) {
        free(sram);
        ReplyError("flush_save: não abriu %s", savePath);
        return;
    }
    size_t done = 0;
    while (done < size) {
        ssize_t n = write(fd, (const char *)sram + done, size - done);
        if (n <= 0)
            break;
        done += (size_t)n;
    }
    bool ok = done == size && fsync(fd) == 0;
    close(fd);
    free(sram);
    if (!ok) {
        ReplyError("flush_save: falha ao gravar %s", savePath);
        return;
    }
    ReplyOk();
}

/* ---------- main ---------- */

static int Usage(const char *argv0)
{
    fprintf(stderr, "uso: %s <rom.gba> --save <arquivo.sav>\n", argv0);
    return 2;
}

int main(int argc, char **argv)
{
    if (argc != 4 || strcmp(argv[2], "--save") != 0)
        return Usage(argv[0]);
    const char *romPath = argv[1];
    const char *savePath = argv[3];

    mLogSetDefaultLogger(&sLogger);

    struct mCore *core = mCoreFind(romPath);
    if (!core) {
        fprintf(stderr, "mgba_runner: ROM não reconhecida: %s\n", romPath);
        return 1;
    }
    if (!core->init(core)) {
        fprintf(stderr, "mgba_runner: falha em core->init\n");
        return 1;
    }
    mCoreInitConfig(core, NULL);

    unsigned width, height;
    core->desiredVideoDimensions(core, &width, &height);
    if (width != SCREEN_W || height != SCREEN_H) {
        fprintf(stderr, "mgba_runner: dimensões inesperadas %ux%u\n", width, height);
        core->deinit(core);
        return 1;
    }
    core->setVideoBuffer(core, sVideoBuffer, SCREEN_W);

    if (!mCoreLoadFile(core, romPath)) {
        fprintf(stderr, "mgba_runner: falha ao carregar %s\n", romPath);
        core->deinit(core);
        return 1;
    }
    if (!mCoreLoadSaveFile(core, savePath, false)) {
        fprintf(stderr, "mgba_runner: falha ao abrir o save %s\n", savePath);
        core->deinit(core);
        return 1;
    }
    core->reset(core);

    char *line = NULL;
    size_t cap = 0;
    bool quit = false;
    while (!quit && getline(&line, &cap, stdin) != -1) {
        struct Command cmd;
        if (!ParseCommand(line, &cmd)) {
            FreeCommand(&cmd);
            ReplyError("JSON inválido");
            continue;
        }
        const char *name = GetStr(&cmd, "cmd");
        if (!name)
            ReplyError("campo \"cmd\" obrigatório");
        else if (strcmp(name, "frames") == 0)
            CmdFrames(core, &cmd);
        else if (strcmp(name, "keys") == 0)
            CmdKeys(core, &cmd);
        else if (strcmp(name, "read") == 0)
            CmdRead(core, &cmd);
        else if (strcmp(name, "write") == 0)
            CmdWrite(core, &cmd);
        else if (strcmp(name, "screenshot") == 0)
            CmdScreenshot(&cmd);
        else if (strcmp(name, "state_save") == 0)
            CmdStateSave(core, &cmd);
        else if (strcmp(name, "state_load") == 0)
            CmdStateLoad(core, &cmd);
        else if (strcmp(name, "reset") == 0) {
            core->reset(core);
            ReplyOk();
        } else if (strcmp(name, "flush_save") == 0)
            CmdFlushSave(core, savePath);
        else if (strcmp(name, "quit") == 0)
            quit = true;
        else
            ReplyError("comando desconhecido: %s", name);
        FreeCommand(&cmd);
    }
    free(line);

    /* deinit descarrega o ROM e fecha o .sav (mapeado com MAP_SHARED), gravando-o.
     * Fim do stdin sem "quit" também grava o save, mas não responde. */
    core->deinit(core);
    if (quit)
        ReplyOk();
    return 0;
}
