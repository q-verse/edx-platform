"""
Contains helper functions for Qverse registration application.
"""
from csv import reader, Sniffer
import io
import logging

LOGGER = logging.getLogger(__name__)


def get_file_header_row(file_content, encoding):
    """
    Returns fields of header row of the file.

    Arguments:
        file_content (str): File content that has been read from the file
        encoding (str): File encoding format e.g: utf-8, utf-16

    Returns:
        header_row (list): List of fields of the header row of CSV file
    """
    decoded_file = file_content.decode(encoding, 'ignore')
    io_string = io.StringIO(decoded_file)
    dialect = Sniffer().sniff(io_string.readline())
    io_string.seek(0)
    header_row = reader(io_string, delimiter=dialect.delimiter).next()
    return [heading.lower().strip() for heading in header_row]


def get_file_encoding(file_path):
    """
    Returns the file encoding format.

    Arguments:
        file_path (str): Path of the file whose encoding format will be returned

    Returns:
        encoding (str): encoding format e.g: utf-8, utf-16, returns None if doesn't find
                        any encoding format
    """
    try:
        file = io.open(file_path, 'r', encoding='utf-8')
        encoding = None
        try:
            encoding = 'utf-8'
            _ = file.read()
        except UnicodeDecodeError:
            encoding = 'utf-16'

        file.close()
        return encoding

    except IOError as error:
        LOGGER.exception('({}) --- {}'.format(error.filename, error.strerror))
        return None
