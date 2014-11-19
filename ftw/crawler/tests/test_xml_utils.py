from ftw.crawler.testing import XMLTestCase
from ftw.crawler.tests.helpers import get_asset
from ftw.crawler.xml_utils import remove_namespaces
from lxml import etree
import io


NAMESPACED_XML = get_asset('namespaced.xml')


class TestRemoveNamespaces(XMLTestCase):

    def test_removes_namespaces(self):
        namespaced_tree = etree.parse(io.BytesIO(NAMESPACED_XML))
        tree = remove_namespaces(namespaced_tree)
        output_xml = etree.tostring(
            tree, xml_declaration=True, encoding='utf-8')
        expected = """\
        <?xml version='1.0' encoding='utf-8'?>
        <root>
            <node>
                <node>Text</node>
            </node>
        </root>
        """
        self.assertXMLEquals(output_xml, expected)
