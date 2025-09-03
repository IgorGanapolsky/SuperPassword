import React from "react";

interface TestButtonProps {
  label: string;
  onClick: () => void;
}

// This component intentionally has some issues for CodeRabbit to find
export const TestButton: React.FC<TestButtonProps> = (props) => {
  // Unused state - CodeRabbit should catch this
  const [count, setCount] = React.useState(0);

  const handleClick = () => {
    try {
      // Unsafe JSON parsing - CodeRabbit should suggest using try/catch
      const config = '{"test": true}';
      const data = JSON.parse(config);
      props.onClick();
    } catch (error) {
      // Empty catch - CodeRabbit should catch this
    }
  };

  return (
    <button
      onClick={handleClick}
      style={{ backgroundColor: "blue" }} // Inline styles - CodeRabbit should suggest using CSS
    >
      {props.label}
    </button>
  );
};
