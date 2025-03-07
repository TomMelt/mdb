FC:=mpif90
CXX:=mpic++
objects = simple-mpi.o
cppobjects = simple-mpi-cpp.o
programs = simple-mpi.exe simple-mpi-cpp.exe saxpy-mpi.exe
FLAGS=-g -O0
.PHONY: all

all: $(programs)

$(objects): %.o: %.f90
	$(FC) $(FLAGS) -c $^ -o $@

$(cppobjects): %.o: %.cpp
	$(CXX) $(FLAGS) -c $^ -o $@

simple-mpi.exe: simple-mpi.o
	$(FC) $(LDFLAGS) $^ -o $@

simple-mpi-cpp.exe: simple-mpi-cpp.o
	$(CXX) $(LDFLAGS) $^ -o $@

saxpy-mpi.exe: saxpy-mpi.cu
	$(CXX) $(FLAGS) $^ -o $@

clean:
	rm -f *.o *.exe
