from lxml import etree
from unittest2 import TestCase


class XMLTestCase(TestCase):

    def tostring(self, xml):
        return etree.tostring(xml, xml_declaration=True,
                              encoding='utf-8', pretty_print=True)

    def tree_from_str(self, xml):
        parser = etree.XMLParser(remove_blank_text=True)
        root = etree.XML(xml.strip(), parser=parser)
        return root.getroottree()

    def assertXMLEquals(self, expected, actual):
        """Assert two strings of XML are equal by normalizing
        whitespace outside text nodes.
        """
        actual_xml = self.tostring(self.tree_from_str(actual))
        expected_xml = self.tostring(self.tree_from_str(expected))
        return self.assertEquals(expected_xml, actual_xml)
