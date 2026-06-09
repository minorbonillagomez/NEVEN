#ifndef R_EXT_RICONV_H
#define R_EXT_RICONV_H
typedef void *voidp;
voidp R_iconv_open(const char* to, const char* from);
size_t R_iconv(voidp cd, const char **inbuf, size_t *inbytesleft, char **outbuf, size_t *outbytesleft);
int R_iconv_close(voidp cd);
#endif
