#define STRINGIZE(x) STRINGIZE2(x)
#define STRINGIZE2(x) #x
#define mu_assert(message, test) do { if (!(test)) return message " (" __FILE__ ":" STRINGIZE(__LINE__) ")"; } while (0)
#define mu_run_test(test) do { char *message = test(); tests_run++; if (message) return message; } while (0)
#define mu_check(check) do { char *message = (check); if(message) return message; } while(0)
int tests_run = 0;

#include "bsglarray.h"
#include <stdio.h>
#include <string.h>

static char* check_bsgl_array(struct bsgl_array *arr) {
    mu_assert( "error, array_byte_size incorrect", arr->array_byte_size == (arr->element_size * arr->capacity) );
    mu_assert( "error, too many elements", arr->number_of_elements <= arr->capacity );
    mu_assert( "error, negative capacity", arr->capacity >= 0 );
    mu_assert( "error, negative number of elements", arr->number_of_elements >= 0 );

    int number_of_free_indices = 0;
    int number_of_unused_nodes = 0;
    struct bsgl_llnode *node;

    node = arr->free_indices;
    while( node ) {
        mu_assert( "error, free index out of range", node->index >= 0 && node->index <= arr->capacity );
        for(int k=0; k < arr->element_size; k++ ) {
            mu_assert( "error, free index with nonzero memory", arr->data[ node->index * arr->element_size + k ] == 0 );
        }
        ++number_of_free_indices;
        node = node->next;
    }

    node = arr->unused_nodes;
    while( node ) {
        mu_assert( "error, free index out of range", node->index == -1 );
        ++number_of_unused_nodes;
        node = node->next;
    }

    mu_assert( "incorrect number of free indices and unused nodes", (number_of_free_indices + number_of_unused_nodes) == arr->capacity );

    return 0;
}

static char* test_manual_create_fill_and_empty() {
    struct bsgl_array array;
    int index, rv;

    bsgl_array_initialize( &array, 5 );

    mu_assert( "number of elements correct", array.number_of_elements == 0 );

    rv = bsgl_array_add_and_fill( &array, &index, "ABCD", 5 );
    mu_assert( "add and fill success", !rv );
    mu_assert( "first index", index == 0 );
    mu_assert( "data present", !strcmp( "ABCD", (char*)bsgl_array_get( &array, index ) ) );
    mu_assert( "number of elements correct", array.number_of_elements == 1 );
    mu_check( check_bsgl_array( &array ) );

    rv = bsgl_array_add_and_fill( &array, &index, "YESX", 5 );
    mu_assert( "add and fill success", !rv );
    mu_assert( "first index", index == 1 );
    mu_assert( "data present", !strcmp( "YESX", (char*)bsgl_array_get( &array, index ) ) );
    mu_assert( "number of elements correct", array.number_of_elements == 2 );
    mu_check( check_bsgl_array( &array ) );

    rv = bsgl_array_add_and_fill( &array, &index, "HMMX", 5 );
    mu_assert( "add and fill success", !rv );
    mu_assert( "first index", index == 2 );
    mu_assert( "data present", !strcmp( "HMMX", (char*)bsgl_array_get( &array, index ) ) );
    mu_assert( "number of elements correct", array.number_of_elements == 3 );
    mu_check( check_bsgl_array( &array ) );

    rv = bsgl_array_add_and_fill( &array, &index, "TEST", 5 );
    mu_assert( "add and fill success", !rv );
    mu_assert( "first index", index == 3 );
    mu_assert( "data present", !strcmp( "TEST", (char*)bsgl_array_get( &array, index ) ) );
    mu_assert( "number of elements correct", array.number_of_elements == 4 );
    mu_check( check_bsgl_array( &array ) );

    bsgl_array_remove( &array, 0 );
    mu_assert( "number of elements correct", array.number_of_elements == 3 );
    mu_check( check_bsgl_array( &array ) );

    rv = bsgl_array_add_and_fill( &array, &index, "YAYX", 5 );
    mu_assert( "add and fill success", !rv );
    mu_assert( "first index", index == 0 );
    mu_assert( "data present", !strcmp( "YAYX", (char*)bsgl_array_get( &array, index ) ) );
    mu_assert( "number of elements correct", array.number_of_elements == 4 );
    mu_check( check_bsgl_array( &array ) );

    bsgl_array_remove( &array, 2 );
    mu_assert( "number of elements correct", array.number_of_elements == 3 );
    mu_check( check_bsgl_array( &array ) );

    bsgl_array_remove( &array, 3 );
    mu_assert( "number of elements correct", array.number_of_elements == 2 );
    mu_check( check_bsgl_array( &array ) );

    rv = bsgl_array_add_and_fill( &array, &index, "YAYX", 5 );
    mu_assert( "add and fill success", !rv );
    mu_assert( "first index", index == 3 );
    mu_assert( "data present", !strcmp( "YAYX", (char*)bsgl_array_get( &array, index ) ) );
    mu_assert( "number of elements correct", array.number_of_elements == 3 );
    mu_check( check_bsgl_array( &array ) );

    rv = bsgl_array_add_and_fill( &array, &index, "HAHA", 5 );
    mu_assert( "add and fill success", !rv );
    mu_assert( "first index", index == 2 );
    mu_assert( "data present", !strcmp( "HAHA", (char*)bsgl_array_get( &array, index ) ) );
    mu_assert( "number of elements correct", array.number_of_elements == 4 );
    mu_check( check_bsgl_array( &array ) );

    rv = bsgl_array_add_and_fill( &array, &index, "HEHE", 5 );
    mu_assert( "add and fill success", !rv );
    mu_assert( "first index", index == 4 );
    mu_assert( "data present", !strcmp( "HEHE", (char*)bsgl_array_get( &array, index ) ) );
    mu_assert( "number of elements correct", array.number_of_elements == 5 );
    mu_check( check_bsgl_array( &array ) );

    bsgl_array_destroy( &array );

    return 0;
}

static char* all_tests() {
    mu_run_test( test_manual_create_fill_and_empty );
    return 0;
}

int main(int argc, char *argv[]) {
    char *result = all_tests();

    if (result != 0) {
     printf("TEST FAILED: %s\n", result);
    }
    else {
     printf("ALL TESTS PASSED\n");
    }
    printf("Tests run: %d\n", tests_run);

    return result != 0;
}
