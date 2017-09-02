---
layout: default
title: Security
permalink: articles/security.html
abstract:
  This article describes the proposed security features for secure transport and access control of ROS resources such as topics, services, parameters and node name spaces.
author: '[Ruffin White](https://github.com/ruffsl)'
published: true
---

- This will become a table of contents (this text will be scraped).
{:toc}

# {{ page.title }}

<div class="abstract" markdown="1">
{{ page.abstract }}
</div>

Original Author: {{ page.author }}

## Context

Before proposing designs for securing ROS 2 by introducing access control and encryption via underlying transport, this article will first summarize the recent work towards securing ROS 1 and DDS.

## ROS 1 Security

ROS 1 uses centralized discovery mechanism to construct a distributed computation graph and disseminate changes in graph topology. This has had predominant effected in previous approaches used to secure ROS. For those only vaguely familiar with the core infrastructure of ROS 1, a relevant section of the ROS Concepts wiki excerpted below.

*From [wiki.ros.org/ROS/Concepts](http://wiki.ros.org/ROS/Concepts)*

> The Computation Graph is the peer-to-peer network of ROS processes that are processing data together. The basic Computation Graph concepts of ROS are nodes, Master, Parameter Server, messages, services, topics, and bags, all of which provide data to the Graph in different ways.
>
> These concepts are implemented in the ros_comm repository.
>
> **Nodes**: Nodes are processes that perform computation. ROS is designed to be modular at a fine-grained scale; a robot control system usually comprises many nodes... A ROS node is written with the use of a ROS client library, such as roscpp or rospy.
>
> **Master**: The ROS Master provides name registration and lookup to the rest of the Computation Graph. Without the Master, nodes would not be able to find each other, exchange messages, or invoke services.
>
> **Parameter Server**: The Parameter Server allows data to be stored by key in a central location. It is currently part of the Master.

The wire level communication between these components is divided between the XMLRPC layer that is used by the ROS 1 API and then the custom transport used for message exchange.

*From [wiki.ros.org/ROS/Technical Overview](http://wiki.ros.org/ROS/Technical%20Overview)*

> The Master is implemented via XMLRPC, which is a stateless, HTTP-based protocol. XMLRPC was chosen primarily because it is relatively lightweight, does not require a stateful connection, and has wide availability in a variety of programming languages.

In addition to this duality between the ROS 1 API and transport, the ROS API itself was similarly subdivided. This includes a unique API for the master, slave and parameter server.

*From [wiki.ros.org/ROS/Master_Slave_APIs](http://wiki.ros.org/ROS/Master_Slave_APIs)*

> The ROS Master and Slave APIs manage information about the availability of topics and services for ROS, as well as the negotiation of connection transport. They are implemented using XML-RPC and come in a variety of language implementations.

Due to these legacy complexities and mixed levels of separation, efforts to retro fit security capabilities into ROS 1 have never been entirely complete solutions. To illustrate this, some recent related work, as well as their features and shortcomings is described in the following section.

### Related Work

This section enumerates previous related work in designing and incorporating  security capabilities into ROS 1. Among our design goals for securing ROS 2 will be to incorporate the best aspects and lessons learned from each, while avoiding the pitfalls of those specific implementations.

#### SROS1

> SROS is a set of security enhancements for ROS, such as native TLS support for all socket transport within ROS, the use of x.509 certificates permitting chains of trust, definable namespace globbing for ROS node restrictions and permitted roles, as well as covenant user-space tooling to auto generate node key pairs, audit ROS networks, and construct/train access control policies.

* Pros
    * Complete Transport Encryption
        * Leverages TLS/SSL to cypher network traffic
    * Complete Access Control
        * Granular Permission for all Resources
        * Resolution of Identity from node namespace
        * Identity/Resource defined by regular expression
    * Plug-in style architecture
        * Substitution of governance behaviors
        * Harden/sanitize individual ROS API calls
    * Profile auditing and training
        * Security event logging
        * Degrees of compliance from policy modes
        * Policy generation from demonstration
    * Public Key Infrastructure tooling
        * Provides extensive CLI to manage keystore
* Cons
    * Limited ROS client library support
        * Only yet supports rospy
        * Few XMLRPC libraries support TLS sockets
    * Strict Encapsulating Security Payload
        * Authentication-only transport unsupported by TLS
        * Traffic must be cyphered inhibiting performance
    * Resources Information leakage
        * PKI extensions encode permissions
        * Certificates are public for TLS handshake
    * No multi cast support
        * TLS is stateful and relies on TCP
* Resources:
    * [Announcement](https://discourse.ros.org/t/announcing-sros-security-enhancements-for-ros/536)
    * [Documentation](http://wiki.ros.org/SROS)

#### Secure ROS

> Secure ROS uses IPSec in transport mode and modified versions of the ROS master, rospy module and roscpp library to ensure secure communication. At run time, the user can specify authorized subscribers and publishers to topics, setters and getters to parameters and providers (servers) and requesters (clients) of services in the form of a YAML configuration file for the ROS master. Secure ROS allows only authorized nodes to connect to topics, services and parameters listed in the configuration file.

* Pros
    * Complete Transport Encryption
        * Leverages IPSec to cypher network traffic
    * Flexible Encapsulating Security Payload
        * ESP supports authentication-only configurations
        * Improve performance by not cyphering traffic
    * Common ROS client library support
        * Support for rospy and roscpp
    * Public Key Infrastructure tooling
        * Provides extensive CLI to manage keystore
* Cons
    * Partial Access Control
        * Policy governance only enforced by ROS Master
        * Peer-to-peer ROS Slave API still internally exposed
        * Resolution of Identity limited to an IP address
    * No multi cast support
        * Support UDPROS is undocumented
* Resources:
    * [Announcement](https://discourse.ros.org/t/announcing-secure-ros/1744)
    * [Documentation](http://secure-ros.csl.sri.com/)


## ROS 2 Security

In contrast, ROS 2 has no master, nor a parameter server to be a part of it. Additionally there is then no longer a centralized arbiter to control the reservation of namespaces, as was the case in ROS 1 when the master would permit only one node per expanded namespace.

### Secure Transport

#### Keystores

### Access Control

#### Profiles

### Security Logging

#### Auditing

## Plugins

### DDS Security

#### Secure Transport

#### Access Control

#### Security Logging

#### Resources:
* [OMG Specification](http://www.omg.org/spec/DDS-SECURITY)
* [Issue Tracker](http://issues.omg.org/issues/lists/dds-security-rtf)

```
```
