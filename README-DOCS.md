# Concepts

## Router 

Router is a decision point in the Copilot, most queries are going through this router. It decides which sub-system or module should handle the user's query or request. This modular approach allows for more efficient and context-aware responses, ensuring that the user's needs are met with the appropriate level of expertise and relevance. this eliminates the need for defining many tools/functions.


## Router: Dynamic System Prompt (DSP)

The Router is a dynamic system prompt that directs the conversation flow based on the user's input. It acts as a central hub, determining which sub-system or module should handle the user's query or request. This modular approach allows for more efficient and context-aware responses, ensuring that the user's needs are met with the appropriate level of expertise and relevance. these prompts

## Agent Expert / L1 Agent: 

The Agent Expert is a specialized module designed to handle specific types of queries or tasks. Each Agent Expert works in a particular domain or skill set, allowing it to provide accurate and detailed responses. The Router directs the user's input to the most suitable Agent Expert,  after some logical handling

>    Example : Web search, Document search, API Forwarder etc

## Super Agent / L2 Agent:

The Super Agent, also known as the L2 Agent, is a higher-level Abstraction which consumes feeds/ outputs of and Agent Expert. The data consumed by L2 agent is not direct, and may be processing on several higher orders of data.

###### Case: 
3 L1 agent processed 10,000 tokens each to 2,000 token outputs , L2 agent consumes these 6,000 tokens and generates a report of 1000 tokens. L1 may be working parallely, but L2 will work after L1 is done.

> example : Report Generator from web results, Artifacts Processor from previous output
