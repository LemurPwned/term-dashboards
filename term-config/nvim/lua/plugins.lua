return require("lazy").setup({
  {
    "neovim/nvim-lspconfig",
    dependencies = {
      "williamboman/mason.nvim",
      "williamboman/mason-lspconfig.nvim",
      "hrsh7th/nvim-cmp",
      "hrsh7th/cmp-nvim-lsp",
      "L3MON4D3/LuaSnip",
      "saadparwaiz1/cmp_luasnip",
    },
    config = function()
      local cmp_lsp = require("cmp_nvim_lsp")
      local capabilities = cmp_lsp.default_capabilities()

      require("mason").setup()
      require("mason-lspconfig").setup({
        ensure_installed = { "pyright", "ruff", "clangd" },
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
        vim.keymap.set("n", "gd", vim.lsp.buf.definition, opts)
        vim.keymap.set("n", "gr", vim.lsp.buf.references, opts)
        vim.keymap.set("n", "K", vim.lsp.buf.hover, opts)
        vim.keymap.set("n", "<leader>rn", vim.lsp.buf.rename, opts)
        vim.keymap.set("n", "<leader>ca", vim.lsp.buf.code_action, opts)

        if client.name == "pyright" then
          client.server_capabilities.documentFormattingProvider = false
          client.server_capabilities.documentRangeFormattingProvider = false
        end
      end

      vim.lsp.config("pyright", {
        on_attach = on_attach,
        capabilities = capabilities,
      })

      vim.lsp.config("ruff", {
        on_attach = on_attach,
        capabilities = capabilities,
      })

      vim.lsp.config("clangd", {
        on_attach = on_attach,
        capabilities = capabilities,
        cmd = { "clangd", "--fallback-style=LLVM" },
      })

      vim.lsp.enable({ "pyright", "ruff", "clangd" })

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
    dependencies = { "L3MON4D3/LuaSnip", "saadparwaiz1/cmp_luasnip" },
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
        sources = {
          { name = "nvim_lsp" },
          { name = "luasnip" },
        },
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
