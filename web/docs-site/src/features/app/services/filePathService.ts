interface CatalogTree {
  [key: string]: CatalogTree | null;
}

interface NormalizeOptions {
  domain?: string;
  ensureMdExtension?: boolean;
}

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function decodePathSegments(path: string): string {
  return path
    .split('/')
    .map((segment) => {
      try {
        return decodeURIComponent(segment);
      } catch {
        return segment;
      }
    })
    .join('/');
}

function stripQueryHash(path: string): string {
  return path.split(/[?#]/)[0];
}

function normalizeSlashes(path: string): string {
  return path.replace(/\\/g, '/').replace(/\/+/g, '/');
}

function trimDotPrefix(path: string): string {
  let result = path;
  while (result.startsWith('./')) {
    result = result.slice(2);
  }
  return result;
}

class FilePathService {
  private isTreeNode(node: unknown): node is CatalogTree {
    return Boolean(node) && typeof node === 'object' && !Array.isArray(node);
  }

  private unwrapTreeBySegments(tree: CatalogTree, segments: string[]): CatalogTree | null {
    let current: unknown = tree;
    for (const segment of segments) {
      if (!this.isTreeNode(current) || !(segment in current)) {
        return null;
      }
      current = current[segment];
    }
    return this.isTreeNode(current) ? current : null;
  }

  private stripKnownPrefixes(path: string, domain?: string): string {
    const domainPart = domain ? escapeRegExp(domain) : '[^/]+';
    const patterns = [
      new RegExp(`(?:^|/)web/docs-site/public/domains/${domainPart}/docs/`, 'i'),
      /(?:^|\/)web\/docs-site\/public\//i,
      new RegExp(`(?:^|/)public/domains/${domainPart}/docs/`, 'i'),
      new RegExp(`(?:^|/)domains/${domainPart}/docs/`, 'i'),
      new RegExp(`(?:^|/)v2/${domainPart}/category/`, 'i'),
    ];

    for (const pattern of patterns) {
      const match = path.match(pattern);
      if (match && typeof match.index === 'number') {
        return path.slice(match.index + match[0].length);
      }
    }
    return path;
  }

  public normalizeLogicalPath(rawPath: string, options: NormalizeOptions = {}): string {
    if (!rawPath || typeof rawPath !== 'string') {
      return '';
    }

    const { domain, ensureMdExtension = false } = options;
    let normalized = rawPath.trim();
    normalized = stripQueryHash(normalized);
    normalized = normalizeSlashes(normalized);
    normalized = trimDotPrefix(normalized);
    normalized = this.stripKnownPrefixes(normalized, domain);
    normalized = decodePathSegments(normalized);
    normalized = normalized.replace(/^\/+/, '').replace(/\/+$/, '');

    if (ensureMdExtension && normalized && !normalized.toLowerCase().endsWith('.md')) {
      normalized = `${normalized}.md`;
    }

    return normalized;
  }

  public fromFrontendCategoryPath(frontendPath: string, options: NormalizeOptions = {}): string {
    return this.normalizeLogicalPath(frontendPath, {
      ...options,
      ensureMdExtension: options.ensureMdExtension ?? true,
    });
  }

  public toPhysicalDocPath(logicalPath: string, domain: string): string {
    const normalizedLogicalPath = this.normalizeLogicalPath(logicalPath, {
      domain,
      ensureMdExtension: true,
    });
    const encodedPath = normalizedLogicalPath
      .split('/')
      .filter(Boolean)
      .map((part) => encodeURIComponent(part))
      .join('/');
    return `/domains/${domain}/docs/${encodedPath}`;
  }

  public normalizeCatalogTreeRoot(tree: CatalogTree, domain?: string): CatalogTree {
    if (!this.isTreeNode(tree)) {
      return {};
    }

    if (domain) {
      const prefixedDomainsTree = this.unwrapTreeBySegments(tree, ['web', 'docs-site', 'public', 'domains', domain, 'docs']);
      if (prefixedDomainsTree) {
        return prefixedDomainsTree;
      }

      const domainsTree = this.unwrapTreeBySegments(tree, ['domains', domain, 'docs']);
      if (domainsTree) {
        return domainsTree;
      }
    }

    const webPublicTree = this.unwrapTreeBySegments(tree, ['web', 'docs-site', 'public']);
    if (webPublicTree) {
      return webPublicTree;
    }

    return tree;
  }
}

const filePathService = new FilePathService();
export default filePathService;
