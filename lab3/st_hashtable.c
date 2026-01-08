#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define _POSIX_C_SOURCE 200809L

#define INITIAL_TABLE_SIZE 10
#define LOAD_FACTOR_THRESHOLD 0.75

// Hash Table Entry structure
typedef struct HTEntry {
	char *name;
	int position;
	struct HTEntry *next;
} HTEntry;

// Symbol Table structure using Hash Table
typedef struct {
	HTEntry **buckets;
	int capacity;
	int size;
	int next_position;
} SymbolTableHT;


// Function prototypes
SymbolTableHT* st_create();
unsigned int hash_function(const char *str, int capacity);
HTEntry* create_entry(const char *name, int position);
void st_resize(SymbolTableHT *st);
int st_add(SymbolTableHT *st, const char *name);
int st_search(SymbolTableHT *st, const char *name);
void st_display(SymbolTableHT *st);
void st_destroy(SymbolTableHT *st);

// Create a new Symbol Table
SymbolTableHT* st_create() {
	SymbolTableHT *st = (SymbolTableHT*)malloc(sizeof(SymbolTableHT));
	st->capacity = INITIAL_TABLE_SIZE;
	st->size = 0;
	st->next_position = 0;
	st->buckets = (HTEntry**)calloc(st->capacity, sizeof(HTEntry*));
	return st;
}

// Simple hash function djb2 algorithm
unsigned int hash_function(const char *str, int capacity) {
	unsigned long hash = 5381;
	int c;

	while ((c = *str++)) {
		hash = ((hash << 5) + hash) + c; // hash * 33 + c
	}

	return hash % capacity;
}

// Create a new hash table entry
HTEntry* create_entry(const char* name, int position) {
	HTEntry *entry = (HTEntry*)malloc(sizeof(HTEntry));
	entry->name = strdup(name);
	entry->position = position;
	entry->next = NULL;
	return entry;
}

// Resize the hash table when load factor is exceeded
void st_resize(SymbolTableHT *st) {
	int old_capacity = st->capacity;
	HTEntry **old_buckets = st->buckets;

	// Double the capacity
	st->capacity *= 2;
	st->buckets = (HTEntry**)calloc(st->capacity, sizeof(HTEntry*));
	st->size = 0;

	// Rehash all entries
	for (int i = 0; i < old_capacity; i++) {
		HTEntry *entry = old_buckets[i];
		while (entry != NULL) {
			HTEntry *next = entry->next;

			// Rehash
			unsigned int index = hash_function(entry->name, st->capacity);
			entry->next = st->buckets[index];
			st->buckets[index] = entry;
			st->size++;

			entry = next;
		}
	}

	free(old_buckets);
	printf("Hash table resized to capacity: %d\n", st->capacity);
}

// Add symbol to table
int st_add(SymbolTableHT *st, const char *name) {
	// Check if name already exists
	int existing_pos = st_search(st, name);
	if (existing_pos != -1) {
		return existing_pos;
	}

	// Check load factor and resize if needed
	float load_factor = (float)(st->size + 1) / st->capacity;
	if (load_factor > LOAD_FACTOR_THRESHOLD) {
		st_resize(st);
	}

	// Add new entry
	unsigned int index = hash_function(name, st->capacity);
	int position = st->next_position++;

	HTEntry *new_entry = create_entry(name, position);
	new_entry->next = st->buckets[index];
	st->buckets[index] = new_entry;
	st->size++;

	return position;
}

// Search for a symbol in the table
int st_search(SymbolTableHT *st, const char *name) {
	unsigned int index = hash_function(name, st->capacity);
	HTEntry *entry = st->buckets[index];

	while (entry != NULL) {
		if (strcmp(entry->name, name) == 0) {
			return entry->position;
		}
		entry = entry->next;
	}

	return -1;
}

// Display the st
void st_display(SymbolTableHT *st) {
	printf("\n=== SYMBOL TABLE (HASH TABLE) ===\n");
    printf("Size: %d, Capacity: %d, Load Factor: %.2f\n", 
           st->size, st->capacity, (float)st->size / st->capacity);
    printf("%-20s | %-10s | %-10s\n", "Name", "Position", "Bucket");
    printf("-----------------------------------------------\n");
    
    for (int i = 0; i < st->capacity; i++) {
        HTEntry *entry = st->buckets[i];
        while (entry != NULL) {
            printf("%-20s | %-10d | %-10d\n", entry->name, entry->position, i);
            entry = entry->next;
        }
    }
    printf("\n");
}

void st_display_structure(SymbolTableHT *st) {
    printf("\n=== HASH TABLE STRUCTURE ===\n");
    printf("Capacity: %d, Size: %d\n\n", st->capacity, st->size);
    
    for (int i = 0; i < st->capacity; i++) {
        printf("Bucket[%2d]: ", i);
        HTEntry *entry = st->buckets[i];
        
        if (entry == NULL) {
            printf("(empty)\n");
        } else {
            while (entry != NULL) {
                printf("[%s:%d]", entry->name, entry->position);
                if (entry->next != NULL) {
                    printf(" -> ");
                }
                entry = entry->next;
            }
            printf("\n");
        }
    }
    printf("\n");
}

// Destroy the Symbol Table
void st_destroy(SymbolTableHT *st) {
    for (int i = 0; i < st->capacity; i++) {
        HTEntry *entry = st->buckets[i];
        while (entry != NULL) {
            HTEntry *next = entry->next;
            free(entry->name);
            free(entry);
            entry = next;
        }
    }
    free(st->buckets);
    free(st);
}

// Main function for testing
int main() {
    SymbolTableHT *st = st_create();
    
    printf("Symbol Table Management - Hash Table Implementation\n");
    printf("====================================================\n\n");
    
    // Test: Add symbols
    printf("Adding symbols...\n");
    int pos1 = st_add(st, "variable1");
    printf("Added 'variable1' at position: %d\n", pos1);
    
    int pos2 = st_add(st, "count");
    printf("Added 'count' at position: %d\n", pos2);
    
    int pos3 = st_add(st, "sum");
    printf("Added 'sum' at position: %d\n", pos3);
    
    int pos4 = st_add(st, "array");
    printf("Added 'array' at position: %d\n", pos4);
    
    int pos5 = st_add(st, "index");
    printf("Added 'index' at position: %d\n", pos5);
    
    // Test: Add duplicate
    printf("\nAttempting to add duplicate 'count'...\n");
    int pos_dup = st_add(st, "count");
    printf("'count' position: %d (already exists)\n", pos_dup);
    
    // Display table
    st_display(st);
    st_display_structure(st);
    
    // Test: Search
    printf("Searching for symbols...\n");
    int search_pos = st_search(st, "sum");
    if (search_pos != -1) {
        printf("Found 'sum' at position: %d\n", search_pos);
    } else {
        printf("'sum' not found\n");
    }
    
    search_pos = st_search(st, "nonexistent");
    if (search_pos != -1) {
        printf("Found 'nonexistent' at position: %d\n", search_pos);
    } else {
        printf("'nonexistent' not found\n");
    }
    
    // Add more symbols to trigger resize
    printf("\nAdding more symbols (to trigger resize)...\n");
    st_add(st, "result");
    st_add(st, "temp");
    st_add(st, "max");
    st_add(st, "min");
    st_add(st, "value");
    st_add(st, "data");
    st_add(st, "flag");
    st_add(st, "status");
    
    // Display final table
    st_display(st);
    st_display_structure(st);
    
    // Cleanup
    st_destroy(st);
    printf("Symbol Table destroyed. Program terminated.\n");
    
    return 0;
}