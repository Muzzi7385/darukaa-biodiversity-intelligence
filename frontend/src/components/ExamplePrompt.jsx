export default function ExamplePrompt({ text, onClick }) {
  return (
    <button type="button" className="example-prompt" onClick={() => onClick(text)}>
      {text}
    </button>
  )
}
