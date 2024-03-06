import Permanent from './permanent';

const handleClick = () => {
  console.log("a creature was clicked!");
}

const CreaturePermanent = (props) => {
  return (
    <>
      <Permanent {...props} onClick={handleClick}/>
    </>
  )
}

export default CreaturePermanent;
