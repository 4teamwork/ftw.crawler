from lxml import etree
from pkg_resources import resource_stream


XML_TYPES = ['application/xml', 'application/xhtml+xml', 'text/xml']
HTML_TYPES = ['text/html']
MARKUP_TYPES = XML_TYPES + HTML_TYPES


def remove_namespaces(tree):
    xslt_file = resource_stream(
        'ftw.crawler.xml_utils', 'remove_namespaces.xsl')
    xslt = etree.parse(xslt_file)
    transform = etree.XSLT(xslt)
    try:
        ns_free_tree = transform(tree)
    except etree.XSLTApplyError:
        return tree
    return etree.ElementTree(ns_free_tree.getroot())
