import { Card } from './card'

function Exile({owner, content, setSelectedCard}) {
  return (
    <>
      <Card
        id="exileShowCard"
        canDrag="false"
        sx={{
          position: "absolute",
          bottom: 0,
          right: 0,
          margin:"20px",
          height: "40%",
          transform: "rotate(90deg)",
        }}
        imageUrl={(content && content.length) ? content[content.length - 1].imageUrl : ""}
        setSelectedCard={setSelectedCard}
      />
    </>
  );
}
export default Exile;
