from hsrwiki_data_parser.models.book import Book

class BookFormatter:
    def format(self, item: Book) -> str:
        """Formats a Book object into a Markdown string."""
        if not isinstance(item, Book):
            return ""

        md = []
        md.append(f"# {item.name}")
        md.append("\n---\n")

        if item.description:
            md.append(f"_{item.description}_")
            md.append("") # Add a newline for spacing

        if item.content:
            for content_part in item.content:
                if content_part.heading:
                    md.append(f"## {content_part.heading}")
                md.append(content_part.text)
        
        return '\n'.join(md)
