CC = g++

include config.mk

default: progs

all: progs

SRC_DIR = ./moca/src/
BIN_DIR = ./bin/
BOOST_FLAGS = -lboost_date_time -lboost_filesystem -lboost_system -lboost_thread -lpthread
LOCAL_DEPENDENCIES = params genome_table genome string_utils math_functions sequence_utility_functions thirdparty/INIReader thirdparty/ini

LOCAL_TARGETS = extract_sequence_chunks_near_sites fimo_2_sites calculate_site_conservation create_binary_from_wig calculate_site_conservation_server
LOCAL_DEP_OBJECTS = $(LOCAL_DEPENDENCIES:=.o)
LOCAL_TARGET_OBJECTS = $(LOCAL_TARGETS:=.o)

local_dep_objects:
	@echo
	@echo =================================
	@echo =  Building common dependencies =
	@echo =================================
	@echo
	cd $(SRC_DIR) && $(MAKE) $(LOCAL_DEP_OBJECTS)

local_target_objects:
	@echo
	@echo ================================
	@echo =     Building target objs     =
	@echo ================================
	@echo
	cd $(SRC_DIR) && $(MAKE) $(LOCAL_TARGET_OBJECTS)

local_targets:
	@echo
	@echo ================================
	@echo =     Building executables     =
	@echo ================================
	@echo
	make $(LOCAL_TARGETS)
	@mkdir -p $(BIN_DIR)
	@mv $(LOCAL_TARGETS) $(BIN_DIR)


progs: local_target_objects local_dep_objects local_targets

clean:
	rm -rf $(SRC_DIR)*.o
	rm -rf $(BIN_DIR)*

extract_sequence_chunks_near_sites_deps = string_utils params genome_table genome math_functions sequence_utility_functions extract_sequence_chunks_near_sites
extract_sequence_chunks_near_sites_objs = $(addprefix $(SRC_DIR), $(extract_sequence_chunks_near_sites_deps:=.o))
extract_sequence_chunks_near_sites:
	$(CC) -I$(SRC_DIR) $(CCFLAGS) $(extract_sequence_chunks_near_sites_objs) -o extract_sequence_chunks_near_sites

fimo_2_sites_deps = string_utils params genome_table genome sequence_utility_functions fimo_2_sites
fimo_2_sites_objs = $(addprefix $(SRC_DIR), $(fimo_2_sites_deps:=.o))
fimo_2_sites:
	$(CC) -I$(SRC_DIR) $(CCFLAGS) $(fimo_2_sites_objs) -o fimo_2_sites

calculate_site_conservation_deps = string_utils params genome_table math_functions calculate_site_conservation
calculate_site_conservation_objs = $(addprefix $(SRC_DIR), $(calculate_site_conservation_deps:=.o))
calculate_site_conservation:
	$(CC) -I$(SRC_DIR) $(CCFLAGS) $(calculate_site_conservation_objs) -o calculate_site_conservation

create_binary_from_wig_deps = string_utils params genome_table math_functions create_binary_from_wig
create_binary_from_wig_objs = $(addprefix $(SRC_DIR), $(create_binary_from_wig_deps:=.o))
create_binary_from_wig:
	$(CC) -I$(SRC_DIR) $(CCFLAGS) $(create_binary_from_wig_objs) -o create_binary_from_wig

calculate_site_conservation_server_deps = string_utils params genome_table math_functions ini INIReader calculate_site_conservation_server
calculate_site_conservation_server_objs = $(addprefix $(SRC_DIR), $(calculate_site_conservation_server_deps:=.o))
calculate_site_conservation_server:
	$(CC) -I$(SRC_DIR)  $(CCFLAGS) $(calculate_site_conservation_server_objs) -o calculate_site_conservation_server $(BOOST_FLAGS)
