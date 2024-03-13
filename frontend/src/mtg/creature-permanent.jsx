import { useEffect } from 'react';
import Permanent from './permanent';
import { receivedNewGameAction, selectAffectedGameData } from './../store/slice';
import store from './../store/store';

const CreaturePermanent = ({
  controller,
  whoIsAskingAttackTarget, setWhoIsAskingAttackTarget,
  whoIsAskingBlockTarget, setWhoIsAskingBlockTarget,
  combatTargetCard, setCombatTargetCard,
  ...props
}) => {
  const gameData = selectAffectedGameData(store.getState());
  const canAttack = gameData.phase.includes("declare attackers step") &&
                    gameData.whose_turn === controller &&
                    controller === "user" &&
                    !("isAttacking" in props.card.annotations);
  const canBlock = gameData.phase.includes("declare blockers step") &&
                   gameData.whose_turn !== controller &&
                   controller === "user" &&
                   !("isBlocking" in props.card.annotations);
  const canBeBlocked = gameData.phase.includes("declare blockers step") &&
                       gameData.whose_turn === controller &&
                       controller !== "user" &&
                       "isAttacking" in props.card.annotations;
  const hasOtherAttackTarget = 
    gameData.board_state.players
      .filter(player => player.player_name !== controller)
        .some(player => player.battlefield.some(
          card => {
            const typeLine = card.isFlipped ? (card.faces?.back.type_line || "")
                                            : (card.faces?.front.type_line || card.type_line || "");
            return typeLine.toLowerCase().includes("planeswalker") || typeLine.toLowerCase().includes("battle")
          }
        ))

  const handleClick = (event) => {
    // I pray for no banding in future games
    if (event.type !== "click") {
      return;
    }
    if (canAttack) {
      if (whoIsAskingAttackTarget) {
        return;
      }
      if (hasOtherAttackTarget) {
        setWhoIsAskingAttackTarget(props.card);
      } else {
        declareAttack("ned");
      }
    }
    if (canBlock) {
      console.log("please click the creature you want to block")
      if (whoIsAskingBlockTarget) {
        return;
      }
      setWhoIsAskingBlockTarget(props.card);
    }
    if (whoIsAskingBlockTarget && canBeBlocked) {
      declareBlockForBlocker(whoIsAskingBlockTarget.in_game_id, props.card.in_game_id);
      setWhoIsAskingBlockTarget(null);
    }
  }

  const declareAttack = (target) => {
    const newAction = {
      type: "set_annotation",
      targetId: props.card.in_game_id,
      annotationKey: "isAttacking",
      annotationValue: target,
    };
    store.dispatch(receivedNewGameAction(newAction));
  }

  const declareBlockForBlocker = (blocker, target) => {
    const newAction = {
      type: "set_annotation",
      targetId: blocker,
      annotationKey: "isBlocking",
      annotationValue: target,
    };
    store.dispatch(receivedNewGameAction(newAction));
  }

  return (
    <>
      <Permanent {...props} onClick={handleClick}/>
    </>
  )
}

export default CreaturePermanent;
