FC:=mpif90
objects = simple-mpi.o
programs = simple-mpi.exe
.PHONY: all

all: $(programs)

$(objects): %.o: %.f90
	$(FC) -ggdb -c $(FFLAGS) $^ -o $@

simple-mpi.exe: simple-mpi.o
	$(FC) $(LDFLAGS) $^ -o $@

clean:
	rm -f *.o *.exe
