# GitHub Action SHA Value Query Guide

## Background
Security tools like SonarQube recommend using commit SHA instead of tags to reference GitHub Actions, ensuring version immutability and security.

## Quick Query Process

### 1. Query Latest Release Information
```bash
curl -s https://api.github.com/repos/{owner}/{repo}/releases/latest | grep -E '"tag_name"|"target_commitish"'
```

### 2. Query SHA Value for Specific Tag
```bash
curl -s https://api.github.com/repos/{owner}/{repo}/git/refs/tags/{tag} | grep '"sha"'
```

## Common Actions Examples

### softprops/action-gh-release
```bash
# Query latest version
curl -s https://api.github.com/repos/softprops/action-gh-release/releases/latest | grep -E '"tag_name"|"target_commitish"'

# Query SHA for v2 tag
curl -s https://api.github.com/repos/softprops/action-gh-release/git/refs/tags/v2 | grep '"sha"'
```

### actions/checkout
```bash
# Query SHA for v4 tag
curl -s https://api.github.com/repos/actions/checkout/git/refs/tags/v4 | grep '"sha"'
```

## Usage Format
After obtaining the SHA, use it in workflows:
```yaml
uses: owner/repo@{sha} # {original_tag}
```

Example:
```yaml
uses: softprops/action-gh-release@72f2c25fcb47643c292f7107632f7a47c1df5cd8 # v2
```

## Important Notes
1. SHA values are typically 40 characters long
2. Keep the `# {tag}` comment for version identification
3. Official Actions (like actions/*) can maintain tag format as they are maintained by GitHub officially
4. Third-party Actions are recommended to use SHA values for enhanced security
