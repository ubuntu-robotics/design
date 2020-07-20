---
layout: default
title: Security usage of Node Interface Description Language
permalink: articles/security_node_interface_description_language.html
abstract:
  Write me.
author: >
  [Ted Kern](https://github.com/arnatious)

published: true
categories: Security
---

{:toc}


# {{ page.title }}

<div class="abstract" markdown="1">
{{ page.abstract }}
</div>

Original Author: {{ page.author }}


## Background

In the pre-NoDL world of secure ROS 2, the process for launching a node with encrypted traffic was a multi-step process:

1. Generate a keystore directory

    e.g. `ros2 security create_keystore demo_keystore`

2. Generate keys and certificates per node

    e.g. `ros2 security create_key demo_keystore /demo_node`

3. Generate access control policies for each interface of the node

  i.e. crafting a specific policy.xml, a process that can be awful to perform by hand.

4. Generate a permissions document from the access control policy

  e.g. `ros2 security create_permission demo_keystore /demo_node policies/policy.xml`

5. Set environment variables enabling security and defining the keystore

    e.g.
    ```bash
    export ROS_SECURITY_KEYSTORE=~/sros2_demo/demo_keystore
    export ROS_SECURITY_ENABLE=true
    export ROS_SECURITY_STRATEGY=Enforce
    ```

6. Run the node(s)
    e.g. `ros2 run example_program demo`

This process is lengthy and cumbersome, and only gets worse when considering the usage of launch files with multiple, conditionally launched nodes or remapping arguments that will require the user to create keys specific to any namespace pushes or remappings provided. It left huge room for user error, and could possibly silently leave traffic unencrypted.


## NoDL Usage

The [**No**de Interface **D**escription **L**anguage]() provides a simple way to specify how a given node communicates in the ROS 2 network. The node's name, as well as the names and producer/consumer status of its interfaces are exposed. Given this information, the idea of a simple 'secure' launch flag that handles all of the above during invocation of `ros2 launch` or `ros2 run`.

The proposed functionality would work as follows:

Given:

- A package, `example`
  - Containing a program, `talker.py`
    - Containing a node with the default name of `/talker`
       - Publishing a topic named `chatter`
- A nodl manifest `talker.nodl.xml` containing the above information
- A launchfile `talker.launch.py` that launches `talker.py`

The user should be able to invoke:

```bash
ros2 launch --secure example talker.launch.py
```

and have steps 1-4 above automatically be run and configured properly. The required information about node and topic naming will be found by searching the ament index for the package's exported nodl.xml file.

## Proposed Implementation in `launch_ros`
The `launch_ros` cli, `ros2launch`, will contain several new named arguments.

- `--secure`, *optional*, boolean flag indicating the launch should be performed in a secure fashion
- `--keystore`, *optional*, used to specify the directory to use as a keystore, creating it if necessary
  - if omitted, will use the `ROS_SECURITY_KEYSTORE` environment variable, throwing an error if unset or invalid
- `--nodl`, *optional*, to specify a specific nodl file in the case of files containing conflicting definitions
  - if omitted, will parse all valid nodl files in each package and combine their node lists

Logic for the proposed functionality requires information about the packages used, to look up the node information in their contained NoDL manifests, as well as any remappings performed either in the launch file or specified by the user at the command line.

### Existing Data Flow
Consider the following launch file, `example.launch.py`:

```python
from launch import LaunchDescription
import launch_ros.actions

def generate_launch_description():
    return LaunchDescription([
        launch_ros.actions.Node(
            package='demo_nodes_cpp', executable='talker', output='screen', name='mouth', namespace='tester', remappings=[('chatter', 'blather')]),
        launch_ros.actions.Node(
            package='demo_nodes_cpp', executable='listener', output='screen', name='ear', namespace='tester', remappings=[('chatter', 'blather')]),
    ])

```

An example invocation of this file follows:

```
$ ros2 launch example.launch.py
.
├── .
└── ros2launch.LaunchCommand.main()
    ├── launch_file: "example.launch.py"
    ├── launch_arguments: []
    ├── ros2launch.api.launch_a_launch_file()
    └── ...
```

Continuing into launch_a_launch_file:

```
.
├── .
└── ros2launch.api.launch_a_launch_file()
    ├── launch_file_path: 'example.launch.py'
    ├── launch_file_arguments: []
    ├── launch_service: <launch.LaunchService>
    ├── parsed_launch_arguments: {}
    └── launch_description: <launch.LaunchDescription>
        └── <launch.actions.IncludeLaunchDescription>
            └── launch_description_source:
                └── location: 'tmp/example.launch.py`
```

The `ros2launch.api.launch_a_launch_file` receives the `path` and `launch_arguments` variable, and creates an `launch.LaunchService()` object that will handle the actual process launching. On construction, the launchservice stores the launch_arguments.

The launch_arguments are parsed, ensuring they are in the form of `foo:=bar`, and a dict is formed as `parsed_launch_args`.

A `launch.LaunchDescription` is then formed, containing an action to import the launch file we specified. `parsed_launch_arguments` is passed along to this `IncludeLaunchDescription` action.

The LaunchService recieves the LaunchDescription and processes the descriptions aynscronously after its `run()` method is called. The service visits each action in the launch description, running the relevant `execute()` method. A variable, `context`, contains a number of entries that are shared across all methods invoked by the LaunchService. Many of these are name mangled.

The call graph of the launch service looks similar to as follows:

```
.
└── IncludeLaunchDescription.visit()
    └── IncludeLaunchDescrption.execute()
        └── get_launch_description_from_python_launch_file()
            └── example.generate_launch_description()
```

At this point, the launch file we specified on the CLI is first accessed, and our nodes are created within a new LaunchDescription.

```
.
└── launch_ros.actions.Node() 'talker'
    ├── cmd: List[]
    │   ├── 0: <launch_ros.substitution.ExecutableInPackage>
    │   ├── 1: '--ros-args'
    │   ├── 2: '-r'
    │   └── 3: <launch.substitution.LocalSubstitution>: "ros_specific_arguments['remaps'][0]"
    ├── __executable: 'talker'
    ├── __package: 'demo_nodes_cpp'
    ├── __node_name: 'mouth'
    ├── __node_namespace: 'tester'
    ├── __remappings: ('chatter', 'blahblah')
    ├── __expanded_node_name: '<node_name_unspecified>'
    ├── __final_node_name: None
    ├── __expanded_remappings: None
    └── __substitutions_performed: False
```

(Not all fields are shown)

Once the nodes are created and `IncludeLaunchDescription.execute()` returns, the LaunchService will eventually visit the Nodes that were just created. The very first step of `Node.execute()` performs substitutions. If the nodes had names or namespaces specified, or remapped elsewhere, they would be resolved after this step, and the above fields would be populated.

After `_perform_substitutions()`:
```
# launch_ros.actions.Node() 'talker'
## __node_namespace: 'tester'
## __expanded_node_namespace: '/tester'
## __expanded_node_name: 'mouth'
## __final_node_name: '/tester/mouth'
## __expanded_remappings: [('chatter', 'blather')]
```

At this point, we have a complete picture of how the launch file will change the expected interfaces from how they were originally named. Any value that wasn't remapped will remain as an empty string, or contain `<node_name_unspecified>`

### NoDL in the picture

The process of launching any given executable gives us

- The package
- The executable name
- A final node name
  - Potentially templated, e.g.
    - `/foo/<node_name_unspecified>`
    - `/<node_name_unspecified>`

We're lacking the information of *what* node we actually launched in that executable. Without that, we can't resolve the final node name in the templated case and we don't know what interfaces to generate policies for.

NoDL fills this knowledge gap. With it, we can look in the **package** for a NoDL file, search Node entries for our **executable** name, get the default node name to substitute into the **template**, and have the interfaces needed for policy generation.

We need the keys and certificates to be generated before the Node is actually launched, which means that the function `Node.execute()` is both the earliest point we have all information needed and the last point before the Node spins up.

### Implementation
Since the keystore will be shared by all nodes launched in a specific launch file, we'll want to create it before any individual node needs it, and set the `ROS_SECURITY_KEYSTORE` environment variable. When individual nodes create keys and certs, they'll be able to find the path to the keystore through the environment variable. We could also attempt to pass it through to a point where it can be placed in the `context` variable available to actions, but this would involve either hacking it into the `launch_file_arguments` argument in `launch_a_launch_file()`, or adding a new argument entirely.

Once at the point of key and cert creation, the `actions.Node` will use the NoDL api to lookup the `NoDL.Node` it is associated with. It will pass the package and executable name, and NoDL will handle searching the package share dir, parsing any/all NoDL files, and finding which `NoDL.Node` has a matching `executable` attribute.

The `actions.Node` will then be able to pass its `__final_node_name` attribute to the `NoDL.Node`, which will perform any template expansion necessary and rename itself and its interfaces to match the names they'll have in the ROS graph.

The `actions.Node` will then create keys using `NoDL.Node.name`.

At this point, any traffic between nodes launched using this method will be fully encrypted, as verified by inspecting them in e.g. wireshark.