#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <memory.h>

void memdump(void *buf, size_t size);

int main(int argc, char **argv)
{
	FILE *fp;
	char *buf;
	long seeker;

	if (argc <= 1) {
		return 1;
	}

	fp = fopen(argv[1], "r");
	if (!fp) {
		return 2;
	}

	(void)fseek(fp, 0L, SEEK_END);
	seeker = ftell(fp);
	buf = malloc((size_t)seeker + (size_t)1);
	if (!buf) {
		(void)fclose(fp);
		return 3;
	}

	(void)fseek(fp, 0L, SEEK_SET);
	(void)fread(buf, 1, (size_t)seeker, fp);

	memdump(buf, (size_t)seeker);

	free(buf);
	(void)fclose(fp);
	return 0;
}

void memdump(void *buf, size_t size)
{
	#define X_WIDTH 16

	size_t i, j;
	unsigned char tmp;
	unsigned char data[X_WIDTH];
	char out[128];
	int idx = 0;
	memset(data, 0, sizeof(data));
	memset(out, 0, sizeof(out));

	for (i = 0; i < size; i++) {
		tmp = ((unsigned char *)buf)[i];
		idx += snprintf(&out[idx], sizeof(out) - idx, "%02X ", tmp);

		if (isprint(tmp)) {
			data[i % X_WIDTH] = tmp;
		}
		else {
			data[i % X_WIDTH] = '.';
		}

		if ((i + 1) % X_WIDTH == 0) {
			out[idx++] = '\t';
			for (j = 0; j < X_WIDTH; j++) {
				out[idx++] = data[j];
			}
			memset(data, 0, sizeof(data));
			printf("%s\n", out);
			memset(out, 0, sizeof(out));
			idx = 0;
		}
	}

	printf("%s", out);
	memset(out, 0, sizeof(out));
	idx = 0;
	for (; i % X_WIDTH != 0; i++) {
		idx += snprintf(&out[idx], sizeof(out) - idx, "00 ");
		data[i % X_WIDTH] = '.';
	}

	if (i % X_WIDTH == 0) {
		out[idx++] = '\t';
		for (j = 0; j < X_WIDTH; j++) {
			out[idx++] = data[j];
		}
		memset(data, 0, sizeof(data));
	}
	printf("%s\n", data);

	#undef X_WIDTH
}
