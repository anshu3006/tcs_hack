import Editor from '@monaco-editor/react';

export default function CodeEditor({ code, onChange, language = 'python', height = '100%' }) {
  const monacoLang = language === 'javascript' ? 'javascript' : language === 'openapi' ? 'yaml' : 'python';

  return (
    <div className="editor-wrapper" style={{ height }}>
      <Editor
        height="100%"
        language={monacoLang}
        value={code}
        onChange={(val) => onChange(val || '')}
        theme="vs-dark"
        options={{
          fontSize: 13,
          fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
          minimap: { enabled: false },
          scrollBeyondLastLine: false,
          padding: { top: 16, bottom: 16 },
          lineNumbers: 'on',
          glyphMargin: false,
          folding: true,
          lineDecorationsWidth: 12,
          lineNumbersMinChars: 3,
          renderLineHighlight: 'line',
          cursorBlinking: 'smooth',
          cursorSmoothCaretAnimation: 'on',
          smoothScrolling: true,
          wordWrap: 'on',
          tabSize: 4,
          bracketPairColorization: { enabled: true },
          autoClosingBrackets: 'always',
        }}
      />
    </div>
  );
}
