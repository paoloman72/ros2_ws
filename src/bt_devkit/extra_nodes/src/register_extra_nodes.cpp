#include "bt_devkit/extra_nodes/register_extra_nodes.hpp"

#include "bt_devkit/extra_nodes/example_node.hpp"

namespace bt_devkit
{

void register_extra_nodes(BT::BehaviorTreeFactory & factory)
{
  factory.registerNodeType<ExampleNode>("ExampleNode");
  // TODO: register your extra nodes here:
  // factory.registerNodeType<MyOtherNode>("MyOtherNode");
}

}  // namespace bt_devkit
