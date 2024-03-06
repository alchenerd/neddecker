import { useState, useEffect } from 'react';
import Box from '@mui/material/Box';
import { useDrag } from 'react-dnd';
import { ItemTypes } from './constants';
import CardContextMenu from './card-context-menu';
import Popover from '@mui/material/Popover';
import Typography from '@mui/material/Typography';
import { receivedNewGameAction } from './../store/slice';
import store from './../store/store';

export function Card({
  card,
  backgroundColor,
  setFocusedCard,
  contextMenuFunctions,
  ...props
}) {
  const isFlipped = card?.annotations?.flipped || false;
  const typeLine = isFlipped ? (card?.faces?.back.type_line || "")
                             : (card?.faces?.front.type_line || card?.type_line || "");
  const manaCost = isFlipped ? (card?.faces?.back.mana_cost || "")
                             : (card?.faces?.front.mana_cost || card?.mana_cost || "");
  const [isFocused, setIsFocused] = useState(false);
  const [contextMenu, setContextMenu] = useState(null);
  const [anchorEl, setAnchorEl] = useState(null);
  const openCAPopover = Boolean(anchorEl);
  const imageSource = isFlipped ? (card?.faces?.back.card_image_uri || "")
                                : (card?.card_image_uri || card?.faces?.front.card_image_uri || "");
  const handleContextMenu = (e) => {
    e.preventDefault();
    setContextMenu(
      contextMenu === null
      ? {
        mouseX: e.clientX + 2,
        mouseY: e.clientY - 6,
        }
      : null,
    )
  };
  const getItemTypeByTypeLine = () => {
    if (card?.triggerContent) {
      return ItemTypes.MTG_TRIGGER;
    }
    if (!typeLine) {
      return null;
    }
    if (typeLine.toLowerCase().indexOf("land") !== -1) {
      return ItemTypes.MTG_LAND_CARD;
    } else if (typeLine.toLowerCase().indexOf("sorcery") !== -1) {
      return ItemTypes.MTG_SORCERY_CARD;
    } else if (typeLine.toLowerCase().indexOf("instant") !== -1) {
      return ItemTypes.MTG_INSTANT_CARD;
    } else {
      return ItemTypes.MTG_NONLAND_PERMANENT_CARD
    }
  }
  const [{ isDragging }, drag] = useDrag(() => ({
    type: getItemTypeByTypeLine() || ItemTypes.MTG_CARD,
    item: {
      in_game_id: card?.in_game_id,
      typeLine: typeLine,
      type: getItemTypeByTypeLine(),
    },
    collect: (monitor) => ({
      isDragging: !!monitor.isDragging()
    }),
      canDrag: props.canDrag === undefined ? true : false,
  }))

  const registerFocus = () => {
    setIsFocused(true);
  }

  useEffect(() => {
    if (isFocused) {
      setFocusedCard?.(card);
    }
    setIsFocused(false);
  }, [isFocused]);

  const handlePopoverOpen = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handlePopoverClose = (event) => {
    setAnchorEl(null);
  };

  const ListCounters = () => {
    if (card?.counters && card?.counters.length) {
      return (
        <>
          <Typography>Counters</Typography>
          {card?.counters.map((counter) => (
            <Typography key={counter.type}>
              {counter.type}: {counter.amount}
            </Typography>
          ))}
        </>
      )
    }
  }

  const removeFromStack = () => {
    store.dispatch(receivedNewGameAction({type: "remove_trigger", targetId: card.in_game_id}));
  };
  const triggerFunctions = [ { name: "remove from stack", _function: removeFromStack, }, ];

  const ListAnnotations = () => {
    console.log(card?.annotations)
    if (card?.annotations && Object.keys(card?.annotations).filter((key) => key !== "isTapped").length) {
      return (
        <>
          <Typography>Annotations</Typography>
          {Object.keys(card?.annotations).filter((key) => key !== "isTapped").map((key) => (
            <Typography key={key}>
              {key}: {String(card?.annotations[key])}
            </Typography>
          ))}
        </>
      )
    }
    return null
  }

  const TriggerOverlay = () => {
    if (card?.triggerContent) {
      return (
        <Box
          sx={{
            position: "absolute",
            backgroundColor: "rgba(0,0,0,0.5)",
            height: "100%",
            width: "100%",
            overflow: "hidden",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <Box
            sx={{
              backgroundColor: "black"
            }}
          >
            <Typography>
              {card.triggerContent}
            </Typography>
          </Box>
        </Box>
      );
    }
  };

  return (
    <>
      <Box
        sx={{
          height: '100%',
          display: "inline-block",
          position: "relative",
          aspectRatio: 2.5 / 3.5,
          overflow: 'hidden',
          backgroundColor: backgroundColor || 'transparent',
          borderRadius: "4%",
          transform: card?.annotations?.isTapped ? "rotate(90deg)" : "",
          ...props.sx,
        }}
        id={card?.in_game_id}
        ref={drag}
        onMouseOver={registerFocus}
        onDoubleClick={props?.onDoubleClick}
        onContextMenu={handleContextMenu}
        onMouseEnter={handlePopoverOpen}
        onMouseLeave={handlePopoverClose}
      >
        <TriggerOverlay />
          <img
            src={imageSource}
            alt={card?.name}
            height='100%'
            style={{
              opacity: isDragging? 0.5 : 1,
              aspectRatio: 2.5 / 3.5,
            }}
          />
        <CardContextMenu {
          ...{
            contextMenu,
            setContextMenu
          }}
          functions={ card?.triggerContent ? triggerFunctions : contextMenuFunctions }
        />
      </Box>
      <Popover id="counter-annotation-popover"
        open={openCAPopover && (card?.counters?.length > 0 || Object.keys(card?.annotations || {}).filter((key) => key !== "isTapped").length > 0)}
        anchorEl={anchorEl}
        sx={{
          pointerEvents: 'none',
        }}
        anchorOrigin={{
          vertical: 'center',
          horizontal: 'right',
        }}
        transformOrigin={{
          vertical: 'center',
          horizontal: 'left',
        }}
        onClose={handlePopoverClose}
        disableRestoreFocus
      >
        <ListCounters />
        <ListAnnotations />
      </Popover>
    </>
  );
}
