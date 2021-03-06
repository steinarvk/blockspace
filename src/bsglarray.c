#include "bsglarray.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>

#define MAX(a,b) (((a)>(b))?(a):(b))
#define MIN(a,b) (((a)<(b))?(a):(b))

int bsgl_array_initialize( struct bsgl_array *arr, int element_size ) {
    arr->element_size = element_size;
    arr->array_byte_size = 0;
    arr->capacity = 0;
    arr->number_of_elements = 0;
    arr->data = NULL;
    arr->free_indices = NULL;
    arr->unused_nodes = NULL;
    arr->node_pages = NULL;
    arr->virtual_to_real = NULL;
    arr->real_to_virtual = NULL;

    return 0;
}

void* bsgl_allocate_memory_page( struct bsgl_memory_page** pages, size_t sz) {
    size_t real_size = sz + sizeof **pages;
    struct bsgl_memory_page *rv = malloc( real_size );
    if( !rv ) {
        return NULL;
    }
    rv->size = real_size;
    rv->next = *pages;
    *pages = rv;
    return (void*)(rv+1);
}

void bsgl_free_memory_pages( struct bsgl_memory_page **pages ) {
    while( *pages ) {
        struct bsgl_memory_page* page = *pages;
        *pages = page->next;
        free( page );
    }
}

void bsgl_array_destroy( struct bsgl_array *arr ) {
    bsgl_free_memory_pages( &arr->node_pages );
    free( arr->data );
    arr->data = NULL;
}

int bsgl_array_reserve( struct bsgl_array *arr, int n ) {
    if( arr->capacity >= n ) {
        return 0;
    }

    if( (2 * arr->capacity) > n ) {
        n = 2 * arr->capacity;
    }

    int new_byte_size = n * arr->element_size;
    unsigned char *new_data = realloc( arr->data, new_byte_size );
    if( !new_data ) {
        return 1;
    }

    size_t excess_size = new_byte_size - arr->array_byte_size;
    memset( &new_data[ arr->array_byte_size ], 0, excess_size );
    arr->data = new_data;
    arr->array_byte_size = new_byte_size;

    int new_index_map_size = n * sizeof arr->virtual_to_real[0];
    int *new_vtr = realloc( arr->virtual_to_real, new_index_map_size );
    if( !new_vtr ) {
        return 1;
    }
    arr->virtual_to_real = new_vtr;
    int *new_rtv = realloc( arr->real_to_virtual, new_index_map_size );
    if( !new_rtv ) {
        return 1;
    }
    arr->real_to_virtual = new_rtv;

    int number_of_new_nodes = n - arr->capacity;
    struct bsgl_llnode *nodes;
    size_t nodes_sz = number_of_new_nodes * sizeof *nodes;
    nodes = bsgl_allocate_memory_page( &arr->node_pages, nodes_sz );
    if( !nodes ) {
        return 1;
    }

    for(int index = 0; index < number_of_new_nodes; index++) {
        nodes[index].real_index = n - 1 - index;
        nodes[index].virtual_index = n - 1 - index;

        nodes[index].next = arr->free_indices;
        arr->free_indices = &nodes[index];
        arr->capacity++;
    }
    assert( arr->capacity = n );

    return 0;
}

static void *memswap(void *a, void *b, size_t n) {
    unsigned char *a_bytes = a;
    unsigned char *b_bytes = b;

    for(int i=0;i<n;i++) {
        a_bytes[i] ^= b_bytes[i];
        b_bytes[i] ^= a_bytes[i];
        a_bytes[i] ^= b_bytes[i];
    }

    return a;
}

void bsgl_array_remove( struct bsgl_array *arr, int index ) {
    assert( arr->unused_nodes );

    struct bsgl_llnode *node = arr->unused_nodes;
    arr->unused_nodes = node->next;
    node->next = arr->free_indices;

    if( arr->number_of_elements > 1 ) {
        int last_real_index = arr->number_of_elements - 1;
        int tbr_real_index = arr->virtual_to_real[ index ];

//        fprintf( stderr, "swapping real %d virtual %d with real %d virtual %d\n", last_real_index, arr->real_to_virtual[ last_real_index ], arr->virtual_to_real[index], index );

        memswap( &arr->data[ arr->element_size * tbr_real_index ],
                 &arr->data[ arr->element_size * last_real_index ],
                 arr->element_size );

        node->real_index = last_real_index;

        arr->real_to_virtual[ tbr_real_index ] = arr->real_to_virtual[ last_real_index ];
        arr->virtual_to_real[ arr->real_to_virtual[ last_real_index ] ] = tbr_real_index;
    } else {
        memset( (void*)bsgl_array_get( arr, index ), 0, arr->element_size ); 

        node->real_index = arr->virtual_to_real[ index ];
    }

    node->virtual_index = index;

    arr->free_indices = node;

    arr->number_of_elements--;
}

int bsgl_array_add( struct bsgl_array *arr, int *index ) {
    *index = -1;

    if( !arr->free_indices ) {
        if( bsgl_array_reserve( arr, arr->number_of_elements + 1 ) ) {
            return 1;
        }
        assert( arr->free_indices );
    }

    struct bsgl_llnode *node = arr->free_indices;
    arr->free_indices = node->next;

    const int real_index = node->real_index;
    const int virtual_index = node->virtual_index;

//    fprintf( stderr, "adding real %d virtual %d\n", real_index, virtual_index );

    arr->virtual_to_real[ virtual_index ] = real_index;
    arr->real_to_virtual[ real_index ] = virtual_index;

    *index = virtual_index;

    node->next = arr->unused_nodes;
    node->real_index = -1;
    node->virtual_index = -1;
    arr->unused_nodes = node;

    arr->number_of_elements++;

    return 0;
}

unsigned char * bsgl_array_get( struct bsgl_array *arr, int index ) {
    return &arr->data[ arr->virtual_to_real[ index ] * arr->element_size ];
}

int bsgl_array_add_and_fill( struct bsgl_array *arr, int *index, void *data, int len ) {
    int rv = bsgl_array_add( arr, index );
    if( rv ) return rv;
    len = MIN( len, arr->element_size );
    memcpy( bsgl_array_get( arr, *index ), data, len );
    return 0;
}
