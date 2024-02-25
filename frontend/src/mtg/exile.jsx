import { Card } from './card'

function Exile({owner, setFocusedCard}) {
  const content = owner?.exile;
  return (
    <>
      <Card
        id="exileShowCard"
        canDrag="false"
        sx={{
          position: "absolute",
          bottom: 0,
          right: 0,
          height: "100%",
          transform: "rotate(90deg)",
        }}
        card={content ? content[0] : null}
        setFocusedCard={(content && content.length) ? setFocusedCard : null}
      />
    </>
  );
}
export default Exile;
