#ifndef H_BSGL_ARRAY
#define H_BSGL_ARRAY

#include <stddef.h>

struct bsgl_llnode;

struct bsgl_llnode {
    int index;
    struct bsgl_llnode *next;
};

struct bsgl_memory_page;

struct bsgl_memory_page {
    size_t size;
    struct bsgl_memory_page *next;
};

struct bsgl_array {
    int element_size;
    int array_byte_size;
    int capacity;
    int number_of_elements;

    unsigned char *data;
    
    struct bsgl_llnode *free_indices;
    struct bsgl_llnode *unused_nodes;

    struct bsgl_memory_page *node_pages;
};

void bsgl_free_memory_pages( struct bsgl_memory_page** );
void* bsgl_allocate_memory_page( struct bsgl_memory_page**, size_t );

int bsgl_array_initialize( struct bsgl_array*, int element_size );
int bsgl_array_reserve( struct bsgl_array*, int );
void bsgl_array_destroy( struct bsgl_array* );

int bsgl_array_add( struct bsgl_array *arr, int *index );
int bsgl_array_add_and_fill( struct bsgl_array *arr, int *index, void *data, int len);
void bsgl_array_remove( struct bsgl_array *arr, int index );
const unsigned char * bsgl_array_get( struct bsgl_array *arr, int index );



#endif
