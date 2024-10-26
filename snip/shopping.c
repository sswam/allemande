
/* Print the shopping list items to a file stream */
static int print_shopping_list_simple(FILE *stream, char **items, int item_count)
{
	int status = -1;
	int i;
	if (fprintf(stream, "\nShopping list:\n") < 0)
		goto fail;
	for (i = 0; i < item_count; i++)
		if (fprintf(stream, "- %s\n", items[i]) < 0)
			goto fail;
	status = 0;
	goto done;
fail:
	perror("Failed to print simple shopping list");
done:
	return status;
}

