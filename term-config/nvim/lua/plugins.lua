return require("lazy").setup({
  {
    "neovim/nvim-lspconfig",
    dependencies = {
      "williamboman/mason.nvim",
      "williamboman/mason-lspconfig.nvim",
      "hrsh7th/nvim-cmp",
      "hrsh7th/cmp-buffer",
      "hrsh7th/cmp-nvim-lsp",
      "hrsh7th/cmp-path",
      "L3MON4D3/LuaSnip",
      "saadparwaiz1/cmp_luasnip",
    },
    config = function()
      local cmp_lsp = require("cmp_nvim_lsp")
      local capabilities = cmp_lsp.default_capabilities()

      local function get_python_path(root_dir)
        local virtual_env = vim.env.VIRTUAL_ENV
        if virtual_env and virtual_env ~= "" then
          return virtual_env .. "/bin/python"
        end

        for _, path in ipairs({ ".venv", "venv", "env" }) do
          local python = (root_dir or vim.loop.cwd()) .. "/" .. path .. "/bin/python"
          if vim.fn.executable(python) == 1 then
            return python
          end
        end

        if vim.fn.executable("python3") == 1 then
          return vim.fn.exepath("python3")
        end

        return vim.fn.exepath("python")
      end

      local function python_code_action(action)
        return function()
          vim.lsp.buf.code_action({
            apply = true,
            context = {
              only = { action },
              diagnostics = vim.diagnostic.get(0),
            },
          })
        end
      end

      require("mason").setup()
      require("mason-lspconfig").setup({
        ensure_installed = { "pyright", "ruff" },
      })

      local format_on_save_patterns = {
        "*.py",
        "*.c",
        "*.cc",
        "*.cpp",
        "*.cxx",
        "*.h",
        "*.hpp",
      }

      local on_attach = function(client, bufnr)
        local opts = { buffer = bufnr, silent = true }

        local function map(lhs, rhs, desc)
          vim.keymap.set("n", lhs, rhs, vim.tbl_extend("force", opts, { desc = desc }))
        end

        map("gd", vim.lsp.buf.definition, "Go to definition")
        map("gr", vim.lsp.buf.references, "List references")
        map("K", vim.lsp.buf.hover, "Hover documentation")
        map("<leader>rn", vim.lsp.buf.rename, "Rename symbol")
        map("<leader>ca", vim.lsp.buf.code_action, "Code actions")
        map("<leader>f", function()
          vim.lsp.buf.format({
            async = false,
            timeout_ms = 2000,
            bufnr = bufnr,
          })
        end, "Format buffer")

        if client.name == "pyright" then
          client.server_capabilities.documentFormattingProvider = false
          client.server_capabilities.documentRangeFormattingProvider = false
        end

        if vim.bo[bufnr].filetype == "python" then
          map("<leader>co", python_code_action("source.organizeImports"), "Organize imports")
          map("<leader>cf", python_code_action("source.fixAll"), "Fix all")
        end
      end

      vim.lsp.config("pyright", {
        on_attach = on_attach,
        capabilities = capabilities,
        before_init = function(_, config)
          config.settings = config.settings or {}
          config.settings.python = config.settings.python or {}
          config.settings.python.pythonPath = get_python_path(config.root_dir)
        end,
        settings = {
          pyright = {
            disableOrganizeImports = true,
          },
          python = {
            analysis = {
              autoSearchPaths = true,
              useLibraryCodeForTypes = true,
              diagnosticMode = "workspace",
              typeCheckingMode = "basic",
            },
          },
        },
      })

      vim.lsp.config("ruff", {
        on_attach = on_attach,
        capabilities = capabilities,
      })

      if vim.fn.executable("clangd") == 1 then
        vim.lsp.config("clangd", {
          on_attach = on_attach,
          capabilities = capabilities,
          cmd = { "clangd", "--fallback-style=LLVM" },
        })

        vim.lsp.enable("clangd")
      end

      vim.lsp.enable({ "pyright", "ruff" })

      vim.api.nvim_create_autocmd("BufWritePre", {
        pattern = format_on_save_patterns,
        callback = function()
          vim.lsp.buf.format({ async = false, timeout_ms = 2000 })
        end,
      })
    end,
  },
  {
    "hrsh7th/nvim-cmp",
    dependencies = {
      "L3MON4D3/LuaSnip",
      "saadparwaiz1/cmp_luasnip",
      "hrsh7th/cmp-buffer",
      "hrsh7th/cmp-path",
    },
    config = function()
      local cmp = require("cmp")
      local luasnip = require("luasnip")

      cmp.setup({
        snippet = {
          expand = function(args)
            luasnip.lsp_expand(args.body)
          end,
        },
        mapping = cmp.mapping.preset.insert({
          ["<C-Space>"] = cmp.mapping.complete(),
          ["<CR>"] = cmp.mapping.confirm({ select = true }),
          ["<Tab>"] = cmp.mapping.select_next_item(),
          ["<S-Tab>"] = cmp.mapping.select_prev_item(),
        }),
        sources = cmp.config.sources({
          { name = "nvim_lsp" },
          { name = "luasnip" },
          { name = "path" },
        }, {
          { name = "buffer" },
        }),
      })

      cmp.setup.filetype("python", {
        sources = cmp.config.sources({
          { name = "nvim_lsp" },
          { name = "luasnip" },
          { name = "path" },
        }, {
          { name = "buffer" },
        }),
      })
    end,
  },
  {
    "nvim-treesitter/nvim-treesitter",
    build = ":TSUpdate",
    config = function()
      local ok, configs = pcall(require, "nvim-treesitter.configs")
      if not ok then
        return
      end

      configs.setup({
        highlight = { enable = true },
        ensure_installed = {
          "lua",
          "vim",
          "vimdoc",
          "python",
          "cpp",
          "markdown",
          "markdown_inline",
        },
      })
    end,
  },
  {
    "preservim/vim-markdown",
    ft = { "markdown" },
    init = function()
      vim.g.vim_markdown_folding_disabled = 1
      vim.g.vim_markdown_conceal = 0
    end,
  },
  {
    "iamcco/markdown-preview.nvim",
    ft = { "markdown" },
    build = "cd app && npm install",
    init = function()
      vim.g.mkdp_auto_start = 0
      vim.g.mkdp_auto_close = 1
    end,
    config = function()
      local opts = { silent = true, buffer = true }
      vim.keymap.set("n", "<leader>mp", ":MarkdownPreview<CR>", opts)
      vim.keymap.set("n", "<leader>ms", ":MarkdownPreviewStop<CR>", opts)
      vim.keymap.set("n", "<leader>mt", ":MarkdownPreviewToggle<CR>", opts)
    end,
  },
  {
    "hedyhli/markdown-toc.nvim",
    ft = { "markdown" },
    config = function()
      require("mtoc").setup({
        headings = { "##", "###", "####" },
      })

      local opts = { silent = true, buffer = true }
      vim.keymap.set("n", "<leader>mt", ":Mtoc<CR>", opts)
      vim.keymap.set("n", "<leader>mu", ":MtocUpdate<CR>", opts)
    end,
  },
  {
    "MeanderingProgrammer/render-markdown.nvim",
    ft = { "markdown" },
    dependencies = { "nvim-treesitter/nvim-treesitter", "nvim-tree/nvim-web-devicons" },
    config = function()
      require("render-markdown").setup({
        latex = { enabled = false },
      })
    end,
  },
  {
    "nvim-lualine/lualine.nvim",
    dependencies = { "nvim-tree/nvim-web-devicons" },
    config = function()
      require("lualine").setup({
        options = { theme = "auto" },
      })
    end,
  },
  {
    "nvim-telescope/telescope.nvim",
    dependencies = { "nvim-lua/plenary.nvim" },
    config = function()
      local telescope = require("telescope")
      telescope.setup()

      local opts = { silent = true }
      vim.keymap.set("n", "<leader>ff", require("telescope.builtin").find_files, opts)
      vim.keymap.set("n", "<leader>fg", require("telescope.builtin").live_grep, opts)
      vim.keymap.set("n", "<leader>fb", require("telescope.builtin").buffers, opts)
    end,
  },
})
