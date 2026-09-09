#pragma once

#include "behaviortree_cpp/bt_factory.h"

namespace bt_devkit
{

// Registers the devkit's "extra" nodes.
//
// Call this from your project's BT_REGISTER_NODES body, together with your
// own nodes, so the executor (which loads exactly ONE plugin .so per robot)
// sees both sets:
//
//   BT_REGISTER_NODES(factory)
//   {
//     bt_devkit::register_extra_nodes(factory);
//     factory.registerNodeType<MyNode>("MyNode");
//   }
//
// Today the devkit ships only the ExampleNode skeleton (the structure to
// start from). Add your own reusable extra nodes here.
void register_extra_nodes(BT::BehaviorTreeFactory & factory);

}  // namespace bt_devkit
