"""Regression checks for Groot metadata and executable node IDs (no ROS)."""
import importlib.util
from pathlib import Path
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "bt_make_bundle.py"
SPEC = importlib.util.spec_from_file_location("bt_make_bundle", SCRIPT)
bundle = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bundle)


class GrootTreeTests(unittest.TestCase):
    def ids(self, xml):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tree.xml"
            path.write_text(xml, encoding="utf-8")
            return bundle.parse_tree_tags(path)

    def test_models_do_not_require_unused_extra_nodes(self):
        xml = """<root BTCPP_format="4">
          <BehaviorTree ID="Main"><GreetNode who="world"/></BehaviorTree>
          <TreeNodesModel><Action ID="ExampleNode">
            <input_port name="message" type="std::string"/>
          </Action></TreeNodesModel></root>"""
        self.assertEqual(self.ids(xml), {"GreetNode"})
        self.assertEqual(bundle.derive_monitoring(xml), [])

    def test_explicit_action_id_is_checked_and_monitored(self):
        xml = """<root><BehaviorTree ID="Main"><Sequence>
          <Action ID="NavigateToPose"/><Condition ID="BatteryCheck"/>
          <Decorator ID="CustomDecorator"><Action ID="UnknownNode"/></Decorator>
        </Sequence></BehaviorTree></root>"""
        self.assertEqual(self.ids(xml), {
            "Sequence", "NavigateToPose", "BatteryCheck",
            "CustomDecorator", "UnknownNode"})
        self.assertEqual(bundle.derive_monitoring(xml), ["navigate_to_pose"])

    def test_compact_navigation_and_all_subtrees(self):
        xml = """<root><BehaviorTree ID="Main"><SubTree ID="Other"/></BehaviorTree>
          <BehaviorTree ID="Other"><NavigateToPose/></BehaviorTree></root>"""
        self.assertEqual(self.ids(xml), {"SubTree", "NavigateToPose"})
        self.assertEqual(bundle.derive_monitoring(xml), ["navigate_to_pose"])

    def test_metadata_cannot_enable_navigation_monitoring(self):
        xml = """<root><BehaviorTree ID="Main"><GreetNode/></BehaviorTree>
          <TreeNodesModel><Action ID="NavigateToPose"/>
          <NavigateToPose/></TreeNodesModel></root>"""
        self.assertEqual(bundle.derive_monitoring(xml), [])
        self.assertEqual(self.ids(xml), {"GreetNode"})

    def test_bare_behavior_tree(self):
        self.assertEqual(self.ids("<BehaviorTree ID='Main'><GreetNode/></BehaviorTree>"),
                         {"GreetNode"})

    def test_catalog_is_not_a_mission_tree(self):
        with self.assertRaisesRegex(ValueError, "no BehaviorTree"):
            self.ids("<root><TreeNodesModel/></root>")


if __name__ == "__main__":
    unittest.main()
