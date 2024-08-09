from collections.abc import Callable


class StringParser:
    def __init__(self, string: str) -> None:
        self.string = string
        self.i = 0

    def is_done(self):
        """Return true if the stream has been read fully."""
        """Return true if the stream has been read fully."""
        return self.i >= len(self.string)

    def peek(self):
        """
        Return the next character in the stream.

        NOTE: This does not check if the stream has finished already,
        consider using `peeks`
        """
        return self.string[self.i]

    def peeks(self):
        """
        Return the next character in the stream.

        Return None if the stream is done.
        """
        """Provide the next character in the stream (if it exists)."""
        return self.peek() if not self.is_done() else None

    def peek_many(self, count: int = 1):
        """Provide a substring of the next count characters in the stream."""
        return self.string[self.i : self.i + count]

    def consume(self):
        """
        Consume the next character in the stream and increments the cursor.

        NOTE: This does not check if the stream has finished already,
        consider using `consumes`
        """
        self.i += 1
        return self.string[self.i - 1]

    def consumes(self):
        """Consume the next character in the stream (if it exists)."""
        return self.consume() if not self.is_done() else None

    def consume_until(self, predicate: Callable[[str], bool]):
        """
        Consume until the predicate returns true.

        Returns the slice from [current index:index where predicate first returns true].
        NOTE: This does not consume the character that the predicate returned True on.
        """
        start = self.i
        while (not self.is_done()) and (not predicate(self.peek())):
            self.i += 1

        return self.string[start : self.i]

    def skip(self, count: int = 1):
        """Skip the next `count` characters in the stream."""
        self.i += count
