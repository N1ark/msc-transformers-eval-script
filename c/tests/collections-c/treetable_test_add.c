#include "treetable.h"
#include "utils.h"
#include <gillian-c/gillian-c.h>

static TreeTable *table;

int main() {
    treetable_new(cmp, &table);

    int pa = __builtin_annot_intval("symb_int", pa);
    int pb = __builtin_annot_intval("symb_int", pb);
    int pc = __builtin_annot_intval("symb_int", pc);

    char a = (char)__builtin_annot_intval("symb_int", a);

    char str_a[] = {a, '\0'};

    char b = (char)__builtin_annot_intval("symb_int", b);

    char str_b[] = {b, '\0'};

    char c = (char)__builtin_annot_intval("symb_int", c);

    char str_c[] = {c, '\0'};

    ASSUME(a < b);
    ASSUME(b < c);

    treetable_add(table, &pa, str_a);
    treetable_add(table, &pb, str_b);
    treetable_add(table, &pc, str_c);

    ASSERT(1 == treetable_contains_key(table, &pa));
    ASSERT(1 == treetable_contains_key(table, &pc));

    treetable_destroy(table);
}
