#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define _POSIX_C_SOURCE 200809L

// BST Node structure
typedef struct BSTNode {
    char *name;
    int position;
    struct BSTNode *left;
    struct BSTNode *right;
} BSTNode;

// Symbol Table structure using BST
typedef struct {
    BSTNode *root;
    int size;
} SymbolTableBST;

// Function prototypes
SymbolTableBST* st_create();
BSTNode* create_node(const char *name, int position);
BSTNode* insert_node(BSTNode *root, const char *name, int *position, int *found);
int st_add(SymbolTableBST *st, const char *name);
BSTNode* search_node(BSTNode *root, const char *name);
int st_search(SymbolTableBST *st, const char *name);
void inorder_traversal(BSTNode *root);
void st_display(SymbolTableBST *st);
void free_tree(BSTNode *root);
void st_destroy(SymbolTableBST *st);

// Create a new Symbol Table
SymbolTableBST* st_create() {
    SymbolTableBST *st = (SymbolTableBST*)malloc(sizeof(SymbolTableBST));
    st->root = NULL;
    st->size = 0;
    return st;
}

// Create a new BST node
BSTNode* create_node(const char *name, int position) {
    BSTNode *node = (BSTNode*)malloc(sizeof(BSTNode));
    node->name = strdup(name);
    node->position = position;
    node->left = NULL;
    node->right = NULL;
    return node;
}

// Insert a node into BST (recursive)
BSTNode* insert_node(BSTNode *root, const char *name, int *position, int *found) {
    if (root == NULL) {
        *found = 0;
        return create_node(name, *position);
    }
    
    int cmp = strcmp(name, root->name);
    
    if (cmp < 0) {
        root->left = insert_node(root->left, name, position, found);
    } else if (cmp > 0) {
        root->right = insert_node(root->right, name, position, found);
    } else {
        // Name already exists
        *found = 1;
        *position = root->position;
    }
    
    return root;
}

// Add a symbol to the table
int st_add(SymbolTableBST *st, const char *name) {
    int position = st->size;
    int found = 0;
    
    st->root = insert_node(st->root, name, &position, &found);
    
    if (!found) {
        st->size++;
    }
    
    return position;
}

// Search for a node in BST
BSTNode* search_node(BSTNode *root, const char *name) {
    if (root == NULL) {
        return NULL;
    }
    
    int cmp = strcmp(name, root->name);
    
    if (cmp < 0) {
        return search_node(root->left, name);
    } else if (cmp > 0) {
        return search_node(root->right, name);
    } else {
        return root;
    }
}

// Search for a symbol in the table
int st_search(SymbolTableBST *st, const char *name) {
    BSTNode *node = search_node(st->root, name);
    return (node != NULL) ? node->position : -1;
}

// Inorder traversal
void inorder_traversal(BSTNode *root) {
    if (root != NULL) {
        inorder_traversal(root->left);
        printf("%-20s | %-10d\n", root->name, root->position);
        inorder_traversal(root->right);
    }
}

// Display the Symbol Table
void st_display(SymbolTableBST *st) {
    printf("\n=== SYMBOL TABLE (BST) ===\n");
    printf("Size: %d\n", st->size);
    printf("%-20s | %-10s\n", "Name", "Position");
    printf("------------------------------------\n");
    inorder_traversal(st->root);
    printf("\n");
}

// Free all nodes in the tree
void free_tree(BSTNode *root) {
    if (root != NULL) {
        free_tree(root->left);
        free_tree(root->right);
        free(root->name);
        free(root);
    }
}

// Destroy the Symbol Table
void st_destroy(SymbolTableBST *st) {
    free_tree(st->root);
    free(st);
}

int main() {
    SymbolTableBST *st = st_create();

    printf("Symbol Table Management - BST Implementation\n");
    printf("============================================\n\n");

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
    
    // Add more symbols
    printf("\nAdding more symbols...\n");
    st_add(st, "result");
    st_add(st, "temp");
    st_add(st, "max");
    st_add(st, "min");
    
    // Display final table
    st_display(st);
    
    // Cleanup
    st_destroy(st);
    printf("Symbol Table destroyed. Program terminated.\n");
    
    return 0;
}