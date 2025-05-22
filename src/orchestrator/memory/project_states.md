A project usually involves the following stages:

1. Gather requirements.
2. Architect the design.
3. Create tasks
4. Pick the first task 
5. Code and implement according to task description.
6. Test the code.
7. If successful, proceed to the next step. If failure, update code and test the code again. 
8. Review the code. 
9. If successful, proceed to the next step. If failure, update code and test the code again.
10. Pick the next task and repeat steps 5 to 9 until no more tasks are left to be implemented.

## Flowchart

```mermaid
graph TD;
    START --> RQ[Gather Requirements];
    RQ --> AR[Architect the Design];
    AR --> TM[Create Tasks];
    TM --> NT[Pick Next Task];

    subgraph TaskLoop
        NT --> CI[Code and Implement Task];
        CI --> TS[Test the Code];
        TS --> TR[Test Results];
        TR --> |FAIL| CU[Update Code];
        CU --> TS;
        TR --> |SUCCESS| RW[Review the Code];
        RW --> RR[Review Results];
        RR --> |FAIL| CU;
        RR --> |SUCCESS| CK[More Tasks?];
        CK --> |YES| NT;
        CK --> |NO| STOP;
    end
```

A step may request to update memory, if yes then update the memory via team member. MUST only update memory when explicitly asked to memorize, remember etc.

These steps can be invoked from any other step in any stage of a product design. The code, test and review steps may form multiple cycles. 
