import { useEffect } from 'react';
import { cloneDeep } from 'lodash';
import Permanent from './permanent';
import { receivedNewGameAction, selectAffectedGameData } from './../store/slice';
import store from './../store/store';

const NonlandPermanent = ({
  controller,
  whoIsAskingAttackTarget, setWhoIsAskingAttackTarget,
  setOpenInspectGherkinDialog,
  ...props
}) => {
  const gameData = selectAffectedGameData(store.getState());
  const typeLine = props.card.isFlipped ? (props.card.faces?.back.type_line || "")
                                        : (props.card.faces?.front.type_line || props.card.type_line || "");
  const canBeAttacked = gameData.phase.includes("declare attackers step") &&
                        gameData.whose_turn !== controller &&
                        controller !== "user" &&
                        (typeLine.toLowerCase().includes("planeswalker") || typeLine.toLowerCase().includes("battle"));

  const handleClick = (event) => {
    if (event.type !== "click") {
    return;
    }
    console.log("a nonland permanent was clicked!");
    console.log(whoIsAskingAttackTarget);
    console.log(canBeAttacked);
    if (whoIsAskingAttackTarget && canBeAttacked) {
      declareAttackForAttacker(whoIsAskingAttackTarget.in_game_id, props.card.in_game_id);
      setWhoIsAskingAttackTarget(null);
    }
  }

  const declareAttackForAttacker = (attacker, target) => {
    const newAction = {
      type: "set_annotation",
      targetId: attacker,
      annotationKey: "isAttacking",
      annotationValue: target,
    };
    store.dispatch(receivedNewGameAction(newAction));
  }

  return (
    <>
      <Permanent {...props} onClick={handleClick} setOpenInspectGherkinDialog={setOpenInspectGherkinDialog}/>
    </>
  )
}

export default NonlandPermanent;
