## Summary
Brief description of the changes.

## Type of Change
- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to change)
- [ ] Documentation update
- [ ] Code quality improvement (refactoring, renaming, style)

## Related Issues
Closes # (issue number)

## Changes Made
- Change 1
- Change 2

## Testing
- [ ] `.\build.ps1 -Test` passes without errors
- [ ] New tests added for new functionality
- [ ] Manual testing performed (describe below)

### Manual Test Results
_Describe any manual testing done._

## Checklist
- [ ] Code follows the project's [coding standards](docs/sops/coding-standards.md)
- [ ] New code uses `Result<T,E>` for error handling (no raw bool returns)
- [ ] New public functions have Doxygen documentation comments
- [ ] No raw `new`/`delete` — uses `std::unique_ptr` or `std::shared_ptr`
- [ ] GPL v3 copyright header present on all new source files
- [ ] `CHANGELOG.md` updated (if applicable)
