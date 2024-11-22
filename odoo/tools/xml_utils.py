# -*- coding: utf-8 -*-
from lxml import etree
from odoo.tools.misc import file_open
from odoo.exceptions import UserError

def check_with_xsd(tree_or_str, stream):
    raise UserError("Method 'check_with_xsd' deprecated ")


def _check_with_xsd(tree_or_str, stream):
    if not isinstance(tree_or_str, etree._Element):
        tree_or_str = etree.fromstring(tree_or_str)
    xml_schema_doc = etree.parse(stream)
    xsd_schema = etree.XMLSchema(xml_schema_doc)
    try:
        xsd_schema.assertValid(tree_or_str)
    except etree.DocumentInvalid as xml_errors:
        #import UserError only here to avoid circular import statements with tools.func being imported in exceptions.py
        from odoo.exceptions import UserError
        raise UserError('\n'.join(str(e) for e in xml_errors.error_log))


def create_xml_node_chain(first_parent_node, nodes_list, last_node_value=None):
    """ Utility function for generating XML files nodes. Generates as a hierarchical
    chain of nodes (each new node being the son of the previous one) based on the tags
    contained in `nodes_list`, under the given node `first_parent_node`.
    It will also set the value of the last of these nodes to `last_node_value` if it is
    specified. This function returns the list of created nodes.
    """
    res = []
    current_node = first_parent_node
    for tag in nodes_list:
        current_node = etree.SubElement(current_node, tag)
        res.append(current_node)

    if last_node_value is not None:
        current_node.text = last_node_value
    return res

def create_xml_node(parent_node, node_name, node_value=None):
    """ Utility function for managing XML. It creates a new node with the specified
    `node_name` as a child of given `parent_node` and assigns it `node_value` as value.
    :param parent_node: valid etree Element
    :param node_name: string
    :param node_value: string
    """
    return create_xml_node_chain(parent_node, [node_name], node_value)[0]

def cleanup_xml_node(xml_node_or_string, remove_blank_text=True, remove_blank_nodes=True, indent_level=0, indent_space="  "):
    """Clean up the sub-tree of the provided XML node.

    If the provided XML node is of type:
    - etree._Element, it is modified in-place.
    - string/bytes, it is first parsed into an etree._Element
    :param xml_node_or_string (etree._Element, str): XML node (or its string/bytes representation)
    :param remove_blank_text (bool): if True, removes whitespace-only text from nodes
    :param remove_blank_nodes (bool): if True, removes leaf nodes with no text (iterative, depth-first, done after remove_blank_text)
    :param indent_level (int): depth or level of node within root tree (use -1 to leave indentation as-is)
    :param indent_space (str): string to use for indentation (use '' to remove all indentation)
    :returns (etree._Element): clean node, same instance that was received (if applicable)
    """
    xml_node = xml_node_or_string

    # Convert str/bytes to etree._Element
    if isinstance(xml_node, str):
        xml_node = xml_node.encode()  # misnomer: fromstring actually reads bytes
    if isinstance(xml_node, bytes):
        xml_node = etree.fromstring(xml_node)

    # Process leaf nodes iteratively
    # Depth-first, so any inner node may become a leaf too (if children are removed)
    def leaf_iter(parent_node, node, level):
        for child_node in node:
            leaf_iter(node, child_node, level if level < 0 else level + 1)

        # Indentation
        if level >= 0:
            indent = '\n' + indent_space * level
            if not node.tail or not node.tail.strip():
                node.tail = '\n' if parent_node is None else indent
            if len(node) > 0:
                if not node.text or not node.text.strip():
                    # First child's indentation is parent's text
                    node.text = indent + indent_space
                last_child = node[-1]
                if last_child.tail == indent + indent_space:
                    # Last child's tail is parent's closing tag indentation
                    last_child.tail = indent

        # Removal condition: node is leaf (not root nor inner node)
        if parent_node is not None and len(node) == 0:
            if remove_blank_text and node.text is not None and not node.text.strip():
                # node.text is None iff node.tag is self-closing (text='' creates closing tag)
                node.text = ''
            if remove_blank_nodes and not (node.text or ''):
                parent_node.remove(node)

    leaf_iter(None, xml_node, indent_level)
    return xml_node
