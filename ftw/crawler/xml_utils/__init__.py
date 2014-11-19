from lxml import etree
from pkg_resources import resource_stream


def remove_namespaces(tree):
    xslt_file = resource_stream(
        'ftw.crawler.xml_utils', 'remove_namespaces.xsl')
    xslt = etree.parse(xslt_file)
    transform = etree.XSLT(xslt)
    ns_free_tree = transform(tree)
    return etree.ElementTree(ns_free_tree.getroot())
