
## What is this?

This program benchmarks different **Regular Model Checking** algorithms for the verification of regular transition systems. A prime example of such a system is a cloud-based application, where many servers share a resource that can only be accessed by one participant at a time. Ensuring mutual exclusion for the resource among servers requires strict descriptions of how agents can transition into requesting, accessing, and freeing the resource. A predefined protocol captures this rule set. The question in protocols of this kind is whether they consistently satisfy the properties they are supposed to ensure. Established methods like unit testing and fuzzing can never achieve absolute certainty; instead, they can only provide a negative counterexample. In systems where one hundred percent confidence (or formal verification) is required, regular model checking (if applicable) is a suitably powerful technique. This program implements the research efforts of my supervisor, Dr. Christoph Welzel-Mohr, for my bachelor thesis at the Technical University of Munich. A detailed description of what regular model checking is, what the method developed by Dr. Christoph Welzel-Mohr entails, and the algorithms tested in this project can be found in my thesis under **thesis**. 

## Author
- Maximilian Kamps 

## Advisors  
- Prof. Francisco Javier Esparza Estaun (Supervisor)
- Dr. Christoph Welzel-Mohr (Advisor)

## Research Topic Abstract

Regular model checking is a technique for automatically verifying infinite-state systems using regular transition systems. Put simply, regular model checking tests whether an undesired state is reachable from a set of initial states through system transitions. The method used in this program reasons over regular transition systems using inductive statements. Inductive statements are assertions that, if satisfied by a configuration \( c \) (a state of the system), are also satisfied by all reachable configurations \( c' \) from \( c \) via the regular transition system. These statements allow for an approximation of reachability between configurations. A detailed description of the method can be found in the folder **thesis**.

## How to Run the Benchmarks 
The program has been tested on macOS.

1. Optional step: Add your own benchmarks
   - Encode a Regular Transition System in the format specified in the next section, "**File format for benchmark**."
   - Add the file to the folder **Src/benchmark**.
   - Add the file to the list **benchmark** in **Src/Main.py**.

2. Recommended step: Use a virtual environment 
   ```bash
   python3 -m venv env
   source env/bin/activate
   ```

3. Install dependencies
   ```bash
   pip3 install -r requirements.txt
   ```

4. Run the program 
   ```bash
   python3 Main.py
   ```

## File Format for Benchmarks 
The program requires that **Regular Transition Systems** are encoded in the following format. The encoding is exemplified for the token passing protocol (https://simple.wikipedia.org/wiki/Token_passing). The token passing protocol is a method used in network communication to manage access to a shared resource, such as a communication channel. In this protocol, a unique token circulates among nodes in the network, and only the node holding the token can transmit data; once it finishes, the token is passed to the next node, ensuring orderly access and preventing data collisions (https://simple.wikipedia.org/wiki/Token_passing). The behavior of this system can be modeled as a regular transition system. A property of interest that we want to verify for the protocol could be whether the token can ever get lost via transitions of the system (from an initial configuration where one agent has the token). The system was encoded in a .json file containing the following objects: 
- The set of initial configurations encoded in the NFA **initial**. 
- The transition behavior of the system encoded in **transducer**. 
- The NFA **no token** encoding the property "Can the token get lost?" in the list **properties**. 
Note that more than one property can be specified in **properties**. 

```javascript
{
  "description": "A token passing algorithm.",
  "deadlockThreshold": 2,
  "alphabet": ["n", "t"],
  "initial": { // The NFA I specifying the initial configurations 
    "states": [
      "q0",
      "q1"
    ],
    "initialState": "q0",
    "acceptingStates": [
      "q1"
    ],
    "transitions": [
      {
        "origin": "q0",
        "target": "q1",
        "letter": "t"
      },
      {
        "origin": "q1",
        "target": "q1",
        "letter": "n"
      }
    ]
  },
  "transducer": { // The Transducer T specifying transitions of the system 
    "states": ["q0", "q1", "q2"],
    "initialState": "q0",
    "acceptingStates": ["q2"],
    "transitions": [
      {
        "origin": "q0",
        "target": "q0",
        "letter": "n,n"
      }, {
        "origin": "q0",
        "target": "q1",
        "letter": "t,n"
      }, {
        "origin": "q1",
        "target": "q2",
        "letter": "n,t"
      }, {
        "origin": "q2",
        "target": "q2",
        "letter": "n,n"
      }
    ]
  },
  "properties": {
    "notoken": { // The NFA B specifying a set of target configurations
      "states": ["q0", "q1"],
      "initialState": "q0",
      "acceptingStates": ["q0"],
      "transitions": [
        {
          "origin": "q0",
          "target": "q0",
          "letter": "n"
        }, {
          "origin": "q0",
          "target": "q1",
          "letter": "t"
        },
        {
          "origin": "q1",
          "target": "q1",
          "letter": "n"
        }, {
          "origin": "q1",
          "target": "q1",
          "letter": "t"
        }
      ]
    }
}
```