# JSON files are run through jsonproc, which is a tool that converts JSON data to an output file
# based on an Inja template. https://github.com/pantor/inja

AUTO_GEN_TARGETS += $(DATA_SRC_SUBDIR)/wild_encounters.h
$(DATA_SRC_SUBDIR)/wild_encounters.h: $(DATA_SRC_SUBDIR)/wild_encounters.json $(DATA_SRC_SUBDIR)/wild_encounters.json.txt
	$(JSONPROC) $^ $@

$(C_BUILDDIR)/wild_encounter.o: c_dep += $(DATA_SRC_SUBDIR)/wild_encounters.h

AUTO_GEN_TARGETS += $(DATA_SRC_SUBDIR)/region_map/region_map_entries.h
$(DATA_SRC_SUBDIR)/region_map/region_map_entries.h: $(DATA_SRC_SUBDIR)/region_map/region_map_sections.json $(DATA_SRC_SUBDIR)/region_map/region_map_sections.entries.json.txt
	$(JSONPROC) $^ $@

$(C_BUILDDIR)/region_map.o: c_dep += $(DATA_SRC_SUBDIR)/region_map/region_map_entries.h

AUTO_GEN_TARGETS += $(DATA_SRC_SUBDIR)/region_map/region_map_entry_strings.h
$(DATA_SRC_SUBDIR)/region_map/region_map_entry_strings.h: $(DATA_SRC_SUBDIR)/region_map/region_map_sections.json $(DATA_SRC_SUBDIR)/region_map/region_map_sections.strings.json.txt
	$(JSONPROC) $^ $@

$(C_BUILDDIR)/region_map.o: c_dep += $(DATA_SRC_SUBDIR)/region_map/region_map_entry_strings.h

AUTO_GEN_TARGETS += include/constants/region_map_sections.h
include/constants/region_map_sections.h: $(DATA_SRC_SUBDIR)/region_map/region_map_sections.json $(DATA_SRC_SUBDIR)/region_map/region_map_sections.constants.json.txt
	$(JSONPROC) $^ $@

AUTO_GEN_TARGETS += $(DATA_SRC_SUBDIR)/items.h
$(DATA_SRC_SUBDIR)/items.h: $(DATA_SRC_SUBDIR)/items.json $(DATA_SRC_SUBDIR)/items.json.txt
	$(JSONPROC) $^ $@

$(C_BUILDDIR)/item.o: c_dep += $(DATA_SRC_SUBDIR)/items.h

AUTO_GEN_TARGETS += $(DATA_SRC_SUBDIR)/heal_locations.h
$(DATA_SRC_SUBDIR)/heal_locations.h: $(DATA_SRC_SUBDIR)/heal_locations.json $(DATA_SRC_SUBDIR)/heal_locations.json.txt
	$(JSONPROC) $^ $@

$(C_BUILDDIR)/heal_location.o: c_dep += $(DATA_SRC_SUBDIR)/heal_locations.h

AUTO_GEN_TARGETS += include/constants/heal_locations.h
include/constants/heal_locations.h: $(DATA_SRC_SUBDIR)/heal_locations.json $(DATA_SRC_SUBDIR)/heal_locations.constants.json.txt
	$(JSONPROC) $^ $@

# Hack 7 — frente B
AUTO_GEN_TARGETS += $(DATA_SRC_SUBDIR)/wild_encounters_time.h
$(DATA_SRC_SUBDIR)/wild_encounters_time.h: $(DATA_SRC_SUBDIR)/wild_encounters_time.json $(DATA_SRC_SUBDIR)/wild_encounters_time.json.txt
	$(JSONPROC) $^ $@

$(C_BUILDDIR)/wild_encounter.o: c_dep += $(DATA_SRC_SUBDIR)/wild_encounters_time.h

# Hack 8 — LeafGreen exclusives share the slot 50/50 (table generated from wild_encounters.json)
AUTO_GEN_TARGETS += $(DATA_SRC_SUBDIR)/wild_encounters_leafgreen.h
$(DATA_SRC_SUBDIR)/wild_encounters_leafgreen.h: $(DATA_SRC_SUBDIR)/wild_encounters.json tools/wild_leafgreen/gen_swaps.py
	python3 tools/wild_leafgreen/gen_swaps.py $< $@

$(C_BUILDDIR)/wild_encounter.o: c_dep += $(DATA_SRC_SUBDIR)/wild_encounters_leafgreen.h

# Prof. Oak news screen: topics and cards table generated from novidades/cartoes.json
AUTO_GEN_TARGETS += $(DATA_SRC_SUBDIR)/novidades_cartoes.h
$(DATA_SRC_SUBDIR)/novidades_cartoes.h: $(DATA_SRC_SUBDIR)/novidades/cartoes.json tools/novidades/gen_cartoes.py
	python3 tools/novidades/gen_cartoes.py $< $@

$(C_BUILDDIR)/novidades_data.o: c_dep += $(DATA_SRC_SUBDIR)/novidades_cartoes.h

# Achievements and battle journal: ids header and tables generated from conquistas/conquistas.json
# (any .o that includes data/conquistas_ids.h must list it in c_dep, like conquistas_data.o below)
AUTO_GEN_TARGETS += $(DATA_SRC_SUBDIR)/conquistas_ids.h $(DATA_SRC_SUBDIR)/conquistas_tabela.h
$(DATA_SRC_SUBDIR)/conquistas_ids.h: $(DATA_SRC_SUBDIR)/conquistas/conquistas.json tools/conquistas/gen_conquistas.py
	python3 tools/conquistas/gen_conquistas.py $< $@ $(DATA_SRC_SUBDIR)/conquistas_tabela.h

$(DATA_SRC_SUBDIR)/conquistas_tabela.h: $(DATA_SRC_SUBDIR)/conquistas_ids.h ;

$(C_BUILDDIR)/conquistas_data.o: c_dep += $(DATA_SRC_SUBDIR)/conquistas_ids.h $(DATA_SRC_SUBDIR)/conquistas_tabela.h
