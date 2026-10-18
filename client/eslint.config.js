import js from "@eslint/js";
import globals from "globals";
import tseslint from "typescript-eslint";

const oneClock = {
  "no-restricted-syntax": [
    "error",
    {
      selector: "CallExpression[callee.object.name='Date'][callee.property.name='now']",
      message: "One clock (CLAUDE.md rule 1): use now() from src/shared/clock.ts, not Date.now().",
    },
    {
      selector: "NewExpression[callee.name='Date']",
      message: "One clock (CLAUDE.md rule 1): no wall-clock Date in capture code.",
    },
  ],
};

export default tseslint.config(
  { ignores: ["dist/", "node_modules/", "playwright-report/", "test-results/", "src/shared/types.ts"] },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  { languageOptions: { globals: { ...globals.browser } } },
  { files: ["src/capture/**/*.ts", "src/shared/**/*.ts", "src/record/**/*.ts"], rules: oneClock },
  { files: ["*.config.{js,ts}", "tests/**/*.ts"], languageOptions: { globals: { ...globals.node } } },
);
