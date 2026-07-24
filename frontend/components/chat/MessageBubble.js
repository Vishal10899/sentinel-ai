"use client";

import { useMemo } from "react";
import { Copy, Check, RotateCcw } from "lucide-react";
import { Badge } from "../ui";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";

import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";

const SUPPORTED_LANGUAGES = [
  "js",
  "javascript",
  "jsx",
  "ts",
  "typescript",
  "json",
  "python",
  "py",
  "bash",
  "shell",
  "sql",
  "html",
  "css",
];

const KEYWORDS = [
  "const",
  "let",
  "var",
  "function",
  "return",
  "async",
  "await",
  "if",
  "else",
  "switch",
  "case",
  "for",
  "while",
  "break",
  "continue",
  "class",
  "new",
  "try",
  "catch",
  "finally",
  "throw",
  "import",
  "export",
  "from",
  "default",
  "extends",
  "implements",
  "interface",
  "type",
  "public",
  "private",
  "protected",
  "true",
  "false",
  "null",
  "undefined",
  "def",
  "None",
  "True",
  "False",
];

function Inline({ text = "" }) {
  const segments = text.split(
    /(`[^`]+`|\[[^\]]+\]\([^)]+\))/g
  );

  return (
    <>
      {segments.map((segment, index) => {
        if (
          segment.startsWith("`") &&
          segment.endsWith("`")
        ) {
          return (
            <code
              key={index}
              className="rounded bg-black/30 px-1.5 py-0.5 font-mono text-indigo-200"
            >
              {segment.slice(1, -1)}
            </code>
          );
        }

        const link = segment.match(
          /^\[([^\]]+)\]\(([^)]+)\)$/
        );

        if (link) {
          return (
            <a
              key={index}
              href={link[2]}
              target="_blank"
              rel="noopener noreferrer"
              className="text-cyan-300 underline underline-offset-2 hover:text-cyan-200"
            >
              {link[1]}
            </a>
          );
        }

        return segment;
      })}
    </>
  );
}

function HighlightedCode({
  language,
  code,
}) {
  const lang = (language || "").toLowerCase();

  if (!SUPPORTED_LANGUAGES.includes(lang)) {
    return code;
  }

  const regex =
    /(\/\/[^\n]*|#[^\n]*|\/\*[\s\S]*?\*\/|`[^`]*`|'[^']*'|"[^"]*"|\b\d+(?:\.\d+)?\b|\b[A-Za-z_][A-Za-z0-9_]*\b)/g;

  return code.split(regex).map((token, index) => {
    let className = "";

    if (
      token.startsWith("//") ||
      token.startsWith("#") ||
      token.startsWith("/*")
    ) {
      className = "text-slate-500";
    } else if (
      /^['"`]/.test(token)
    ) {
      className = "text-emerald-300";
    } else if (
      /^\d/.test(token)
    ) {
      className = "text-amber-300";
    } else if (
      KEYWORDS.includes(token)
    ) {
      className = "text-violet-300";
    }

    return (
      <span
        key={index}
        className={className}
      >
        {token}
      </span>
    );
  });
}
function CodeBlock({
  language = "",
  code = "",
}) {
  const lang =
    language.trim().toLowerCase() || "text";

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
    } catch (error) {
      console.error("Copy failed:", error);
    }
  };

  return (
    <div className="my-4 overflow-hidden rounded-xl border border-white/10 bg-[#080b12]">
      <div className="flex items-center justify-between border-b border-white/10 bg-[#111827] px-4 py-2">
        <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
          {lang}
        </span>

        <button
          onClick={handleCopy}
          className="flex items-center gap-1 rounded-md px-2 py-1 text-xs text-slate-400 transition hover:bg-white/5 hover:text-white"
        >
          <Copy className="h-3.5 w-3.5" />
          Copy
        </button>
      </div>

      <pre className="overflow-x-auto p-4 text-sm leading-7 text-slate-200">
        <code>
          <HighlightedCode
            language={lang}
            code={code}
          />
        </code>
      </pre>
    </div>
  );
}

function MarkdownText({ text = "" }) {
  const lines = text.split("\n");
  const elements = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    if (!line.trim()) {
      elements.push(
        <div
          key={`space-${i}`}
          className="h-2"
        />
      );
      continue;
    }

    // Headings
    if (/^###\s/.test(line)) {
      elements.push(
        <h3
          key={i}
          className="mt-4 mb-2 text-lg font-semibold"
        >
          <Inline text={line.replace(/^###\s/, "")} />
        </h3>
      );
      continue;
    }

    if (/^##\s/.test(line)) {
      elements.push(
        <h2
          key={i}
          className="mt-5 mb-2 text-xl font-bold"
        >
          <Inline text={line.replace(/^##\s/, "")} />
        </h2>
      );
      continue;
    }

    if (/^#\s/.test(line)) {
      elements.push(
        <h1
          key={i}
          className="mt-6 mb-3 text-2xl font-bold"
        >
          <Inline text={line.replace(/^#\s/, "")} />
        </h1>
      );
      continue;
    }

    // Bullet List
    if (/^[-*]\s/.test(line)) {
      elements.push(
        <div
          key={i}
          className="ml-5 flex gap-2"
        >
          <span>•</span>

          <span>
            <Inline text={line.slice(2)} />
          </span>
        </div>
      );
      continue;
    }

    // Numbered List
    if (/^\d+\.\s/.test(line)) {
      const number =
        line.match(/^\d+\./)?.[0] ?? "";

      elements.push(
        <div
          key={i}
          className="ml-5 flex gap-2"
        >
          <span>{number}</span>

          <span>
            <Inline
              text={line.replace(/^\d+\.\s/, "")}
            />
          </span>
        </div>
      );

      continue;
    }

    // Table
    if (
      line.includes("|") &&
      /^\s*\|?\s*:?-{3,}/.test(lines[i + 1] || "")
    ) {
      const headers = line
        .split("|")
        .filter(Boolean)
        .map((item) => item.trim());

      i += 2;

      const rows = [];

      while (
        i < lines.length &&
        lines[i].includes("|")
      ) {
        rows.push(
          lines[i]
            .split("|")
            .filter(Boolean)
            .map((item) => item.trim())
        );

        i++;
      }

      i--;

      elements.push(
        <div
          key={`table-${i}`}
          className="my-4 overflow-x-auto"
        >
          <table className="w-full border-collapse text-left text-sm">
            <thead>
              <tr>
                {headers.map((header, index) => (
                  <th
                    key={index}
                    className="border border-white/10 bg-white/5 px-3 py-2 font-semibold"
                  >
                    <Inline text={header} />
                  </th>
                ))}
              </tr>
            </thead>

            <tbody>
              {rows.map((row, rowIndex) => (
                <tr key={rowIndex}>
                  {headers.map((_, cell) => (
                    <td
                      key={cell}
                      className="border border-white/10 px-3 py-2"
                    >
                      <Inline
                        text={row[cell] || ""}
                      />
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );

      continue;
    }

    elements.push(
      <p
        key={i}
        className="my-1 whitespace-pre-wrap"
      >
        <Inline text={line} />
      </p>
    );
  }

  return elements;
}
function Markdown({ content = "" }) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      rehypePlugins={[rehypeRaw]}
      components={{
        code({ inline, className, children }) {
          const match = /language-(\w+)/.exec(className || "");

          if (!inline && match) {
            return (
              <div className="relative my-4">
  <button
    onClick={() =>
      navigator.clipboard.writeText(
        String(children).replace(/\n$/, "")
      )
    }
    className="absolute right-3 top-3 z-10 flex items-center gap-1 rounded-md border border-white/10 bg-slate-800 px-2 py-1 text-xs text-slate-300 hover:bg-slate-700"
  >
    <Copy className="h-3 w-3" />
    Copy
  </button>

  <SyntaxHighlighter
    style={oneDark}
    language={match[1]}
    PreTag="div"
    customStyle={{
      margin: 0,
      borderRadius: "12px",
      background: "#080b12",
      padding: "18px",
      paddingTop: "48px",
      fontSize: "13px",
    }}
  >
    {String(children).replace(/\n$/, "")}
  </SyntaxHighlighter>
</div>
            );
          }

          return (
            <code className="rounded bg-black/30 px-1 py-0.5 text-indigo-200">
              {children}
            </code>
          );
        },
      }}
    >
      {content}
    </ReactMarkdown>
  );
}

export default function MessageBubble({
  message,
  onCopy,
  onRetry,
}) {
  const assistant = message.role === "assistant";

  const timestamp = useMemo(() => {
    return new Date(
      message.created_at || Date.now()
    ).toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });
  }, [message.created_at]);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(
        message.content || ""
      );

      onCopy?.(message.content);
    } catch (error) {
      console.error(error);
    }
  };

  return (
    <article
      className={`flex ${
        assistant
          ? "justify-start"
          : "justify-end"
      }`}
    >
      <div
        className={`max-w-[90%] rounded-2xl px-4 py-3 shadow-sm transition-all ${
          assistant
            ? "border border-white/10 bg-white/[0.045]"
            : "bg-indigo-600 text-white"
        }`}
      >
        <div className="break-words text-sm leading-7">
          {assistant ? (
            <Markdown
              content={message.content}
            />
          ) : (
            <p className="whitespace-pre-wrap">
              {message.content}
            </p>
          )}
        </div>

        <div className="mt-4 flex flex-wrap items-center gap-2 text-[11px] text-slate-400">

          {assistant && (
            <>
              <button
                onClick={handleCopy}
                className="inline-flex items-center gap-1 rounded-md px-2 py-1 transition hover:bg-white/5 hover:text-white"
              >
                <Copy className="h-3.5 w-3.5" />
                Copy
              </button>

              {onRetry && (
                <button
                  onClick={onRetry}
                  className="inline-flex items-center gap-1 rounded-md px-2 py-1 transition hover:bg-white/5 hover:text-white"
                >
                  <RotateCcw className="h-3.5 w-3.5" />
                  Retry
                </button>
              )}

              {message.provider && (
                <Badge tone="indigo">
                  {message.provider}
                </Badge>
              )}

              {message.model && (
                <Badge>
                  {message.model}
                </Badge>
              )}

              {message.tokens != null && (
                <Badge tone="emerald">
                  {message.tokens} tokens
                </Badge>
              )}

              {message.latency_ms != null && (
                <Badge tone="slate">
                  {message.latency_ms} ms
                </Badge>
              )}
            </>
          )}

          <span className="ml-auto">
            {timestamp}
          </span>
        </div>
      </div>
    </article>
  );
}