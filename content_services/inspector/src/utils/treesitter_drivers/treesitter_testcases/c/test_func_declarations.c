#if defined(__GNUC__) && defined(__PIC__)
#define inline inline __attribute__((always_inline))
#endif

void *__mmap(void *, size_t, int, int, int, off_t);
int __munmap(void *, size_t);
void *__mremap(void *, size_t, size_t, int, ...);
int __madvise(void *, size_t, int);
clusterNode *createClusterNode(char *nodename, int flags);
int clusterAddNode(clusterNode *node);
void clusterAcceptHandler(aeEventLoop *el, int fd, void *privdata, int mask);
void clusterReadHandler(aeEventLoop *el, int fd, void *privdata, int mask);

// Add a function definition to ensure it's not included in declarations
int some_function() {
    return 42;
}

// Add a variable declaration to ensure it's not picked up as a function
int not_a_function;

// Add a typedef function pointer to ensure it's handled correctly
typedef void (*signal_handler_t)(int);

//function with a complex return type
struct result_type complex_function(void *data, int size);
