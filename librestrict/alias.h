/**
 * alias.h
 *
 * Darwin does not support alias attributes.
 * This header defines a 'safe' (i.e., platform-agnostic) way to create aliases.
 */

/* Create a safe alias for NAME accessible via ALIASNAME. */
#define safe_alias(name, aliasname) _safe_alias(name, aliasname)

/* Darwin does not support alias attributes. */
#ifndef __APPLE__
#define _safe_alias(name, aliasname) \
        extern __typeof (name) aliasname __attribute__ ((alias (#name)))
#else
#define _safe_alias(name, aliasname) \
        __asm__(".globl _" #aliasname); \
        __asm__(".set _" #aliasname ", _" #name); \
        extern __typeof(name) aliasname
#endif
