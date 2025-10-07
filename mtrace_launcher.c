#include <mcheck.h> //mtrace
#include <stdio.h> //printf
#include <stdlib.h> //EXIT_FAILURE
#include <unistd.h> //execl

int main(int argc, char** argv) {
	mtrace();
	if (argc < 2) {
		puts("Argument error! Expected 1 argument: Please provide a path to an executable");
		exit(EXIT_FAILURE);
	}
	argv[argc] = NULL;
	printf("Running %s\n", argv[1]);
	int status = execv(argv[1], argv+1);
	printf("Exec status: %d\n", status);
}
