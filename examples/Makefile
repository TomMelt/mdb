# check if cuda compiler exists
ifneq ($(shell which nvcc 2>/dev/null),)
    HAS_CUDA=true
else
    HAS_CUDA=false
endif

FC:=mpif90
CC:=mpicc
CXX:=mpic++
objects = simple-mpi.o
cppobjects = simple-mpi-cpp.o
programs = simple-mpi.exe simple-mpi-cpp.exe simple-memory.exe
ifeq ($(HAS_CUDA),true)
    programs += saxpy-mpi.exe
endif
FLAGS=-g -O0
.PHONY: all

all: $(programs)

$(objects): %.o: %.f90
	$(FC) $(FLAGS) -c $(FFLAGS) $^ -o $@

$(cppobjects): %.o: %.cpp
	$(CXX) $(FLAGS) -c $(FFLAGS) $^ -o $@

simple-mpi.exe: simple-mpi.o
	$(FC) $(LDFLAGS) $^ -o $@

simple-mpi-cpp.exe: simple-mpi-cpp.o
	$(CXX) $(LDFLAGS) $^ -o $@

simple-memory.exe: simple-memory.c
	$(CC) $(FLAGS) $^ -o $@

ifeq ($(HAS_CUDA),true)
saxpy-mpi.exe: saxpy-mpi.cu
	$(CXX) $(FLAGS) $^ -o $@
endif

clean:
	rm -f *.o *.exe
