program simple
  use mpi

  integer process_rank, size_of_cluster, ierror, tag
  real :: var
  integer :: i

  ierror = 0
  var = 0.

  call mpi_init(ierror)
  call mpi_comm_size(mpi_comm_world, size_of_cluster, ierror)
  call mpi_comm_rank(mpi_comm_world, process_rank, ierror)

  var = 10.*process_rank

  if (process_rank == 0) then
    print *, 'process 0 sleeping for 3s...'
    do i = 1, 3
      call sleep(1)
      print *, i, 's...'
    end do
  end if

  call MPI_BARRIER(mpi_comm_world, ierror);
  call levelone()

  print *, 'internal process: ', process_rank, 'of ', size_of_cluster
  print *, 'var = ', var

  call mpi_finalize(ierror)

  contains

    subroutine levelone()
      implicit none
      print *, 'in level 1'
      call MPI_BARRIER(mpi_comm_world, ierror);
      call leveltwo()
    end subroutine levelone

    subroutine leveltwo()
      implicit none
      print *, 'in level 2'
    end subroutine leveltwo
end program
