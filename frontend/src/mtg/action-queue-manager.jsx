import { useState, useEffect } from 'react';

/*
 * Valid actions:
 * move a card: { type: "move", targetId: "u1#1", from: "hand", to: "battlefield" } // puts a card from A to B, if it's casting a spell, then the destination is `stack`
 * tap a permanent: { type: "tap", targetId: "u1#1" } // set card as `tapped`
 * untap a permanent: { type: "untap", targetId: "u1#1" } // set card as `untapped`
 * create a trigger: { type: "createTrigger", targetId: "u1#1", triggerId: "u1#1t1"} // create a `trigger` pseudo-card and put it on the stack; enter the battle trigger, activate permanent trigger, activate card (like ninjutsu, flashback) all use this action
 * register a delayed trigger: { type: "setDelayedTrigger", targetId: "u1#1", timing: "at the end of controller's next turn", happens: "once" } // register a trigger that will be put on the stack at a predefined timing
 * add mana: { type: "addMana", targetId: "u1#1", mana: ["R"] }
 * declare an attacker: { type: "declareAttacker", targetId: "u1#1" } // annotate target card as `attacking`
 * declare a blocker: { type: "declareBlocker", targetId: "u1#1", blocking: "n1#1" } // annotate target card as `blocking [id of another card]`
 * assign counter to a card: { type: "setCounter", targetId: "u1#1", counterType: "+1/+1", amount: 2 } // set a type of counter of a card to an amount
 * annotate a card: { type: "annotate", targetId: "u1#1", annotation: "White creatures you control gets +1/+1" } // annotate a card for further in-game actions
 * choose modes on a card: { type: "chooseModes", targetId: "u1#1", choices: { "c1u1#1": "Draw a card.", "c2u1#1": "deal 1 damage to target creature" } }
 * choose targets: { type: "chooseTargets", targetId: "c2u1#1", choices: [ "n1#1" ] } // choices may be an array of ids, or an array of key-value pairs of (str: int) as (id: amount)
 * resolve top card/trigger on the stack: { type: "resolve", "targetId": "u1#1", effects: [] } // effects may be indexes of action
 * pay cost for something: { type: "payCost", targetId: "u1#1", costs: []}
 */

function ActionQueueManager() {
  const [actionQueue, setActionQueue] = useState([]);
  const enqueueAction = (action) => {
    if (typeof action !== 'object' || action === null) {
      throw new Error('Invalid action: Must be a non-null object');
    }
    setActionQueue([...actionQueue, action]);
  };
  const removeLastAction = () => {
    setActionQueue((prevActionQueue) => {
      if (prevActionQueue.length > 0) {
        return prevActionQueue.slice(0, -1);
      } else {
        return prevActionQueue;
      }
    });
  };
  const getActionQueue = () => {
    return actionQueue;
  };
  return null;
}

export default ActionQueueManager;
