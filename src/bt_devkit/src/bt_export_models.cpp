#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>

#include "behaviortree_cpp/bt_factory.h"
#include "behaviortree_cpp/xml_parsing.h"

// Separate authoring tool: never constructs or ticks a mission tree.
int main(int argc, char** argv)
{
  if (argc != 3) {
    std::cerr << "Usage: bt_export_models <plugin.so> <output.xml>\n";
    return 2;
  }

  const std::filesystem::path output(argv[2]);
  const std::filesystem::path temporary(output.string() + ".tmp");
  try {
    BT::BehaviorTreeFactory factory;
    factory.registerFromPlugin(argv[1]);
    const auto xml = BT::writeTreeNodesModelXML(factory, false);

    if (!output.parent_path().empty()) {
      std::filesystem::create_directories(output.parent_path());
    }
    std::ofstream stream;
    stream.exceptions(std::ios::failbit | std::ios::badbit);
    stream.open(temporary, std::ios::out | std::ios::trunc);
    stream << xml;
    stream.close();
    std::filesystem::rename(temporary, output);
    std::cout << "Groot2 models: " << output << '\n';
    return 0;
  } catch (const std::exception& error) {
    std::error_code ignored;
    std::filesystem::remove(temporary, ignored);
    std::cerr << "bt_export_models: " << error.what() << '\n';
    return 1;
  }
}
